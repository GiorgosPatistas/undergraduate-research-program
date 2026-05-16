"""
train_and_save.py — XGBoost Training Script
============================================
Τρέξε αυτό το script για να εκπαιδεύσεις το μοντέλο και να αποθηκεύσεις
τα αρχεία που χρειάζεται το ML service.

Απαιτήσεις:
    pip install xgboost shap pandas numpy scikit-learn joblib optuna

Χρήση:
    python train_and_save.py

Έξοδος (μέσα στο φάκελο ml_models/):
    xgboost_model.pkl     — το εκπαιδευμένο XGBoost μοντέλο
    feature_names.pkl     — λίστα με τα ονόματα των features (σειρά σημαίνει)
    categorical_cols.pkl  — ποιες στήλες είναι categorical

Σημείωση:
    Το αρχείο diabetic_data.csv πρέπει να βρίσκεται στον ίδιο φάκελο.
"""

import os
import warnings
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
import optuna
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    roc_auc_score, average_precision_score, brier_score_loss,
    classification_report, precision_recall_curve,
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.utils import resample

warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

# ── 1. Load data ───────────────────────────────────────────────────────────────

print('=' * 60)
print('  SMART HEALTHCARE — XGBoost Training')
print('=' * 60)

DATA_PATH = os.path.join(os.path.dirname(__file__), 'diabetic_data.csv')
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f'diabetic_data.csv not found at {DATA_PATH}\n'
        'Download from: https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008'
    )

print('\n[1/6] Loading data...')
df = pd.read_csv(DATA_PATH)
df.replace('?', np.nan, inplace=True)
print(f'      Dataset: {df.shape[0]:,} rows × {df.shape[1]} columns')

# ── 2. Feature engineering ─────────────────────────────────────────────────────

print('\n[2/6] Feature engineering...')

df_fe = df.copy()
df_fe['target'] = (df_fe['readmitted'] == '<30').astype(int)
print(f'      Readmission <30 days rate: {df_fe["target"].mean():.3%}')

def map_diag(code):
    try:
        code = str(code).strip()
        if code.startswith('V') or code.startswith('E'):
            return 'external'
        c = float(code)
        if 250 <= c < 251:  return 'diabetes'
        if 390 <= c <= 459: return 'circulatory'
        if 460 <= c <= 519: return 'respiratory'
        if 520 <= c <= 579: return 'digestive'
        if 580 <= c <= 629: return 'genitourinary'
        if 710 <= c <= 739: return 'musculoskeletal'
        if 800 <= c <= 999: return 'injury'
        if 140 <= c <= 239: return 'neoplasms'
        return 'other'
    except:
        return 'other'

for col in ['diag_1', 'diag_2', 'diag_3']:
    df_fe[f'{col}_cat'] = df_fe[col].apply(map_diag)

med_cols = ['metformin', 'repaglinide', 'nateglinide', 'chlorpropamide',
            'glimepiride', 'glipizide', 'glyburide', 'pioglitazone',
            'rosiglitazone', 'acarbose', 'insulin']

df_fe['total_prior_visits'] = (
    df_fe['number_outpatient'] + df_fe['number_emergency'] + df_fe['number_inpatient']
)
df_fe['num_med_changes'] = df_fe[med_cols].apply(
    lambda row: sum(1 for v in row if v in ['Up', 'Down']), axis=1
)
df_fe['procedures_per_day'] = df_fe['num_procedures'] / (df_fe['time_in_hospital'] + 1)

age_map = {
    '[0-10)': 5,  '[10-20)': 15, '[20-30)': 25, '[30-40)': 35, '[40-50)': 45,
    '[50-60)': 55, '[60-70)': 65, '[70-80)': 75, '[80-90)': 85, '[90-100)': 95,
}
df_fe['age_numeric']          = df_fe['age'].map(age_map)
df_fe['age_x_medications']    = df_fe['age_numeric'] * df_fe['num_medications']
df_fe['hospital_x_diagnoses'] = df_fe['time_in_hospital'] * df_fe['number_diagnoses']
df_fe['age_x_inpatient']      = df_fe['age_numeric'] * df_fe['number_inpatient']
df_fe['meds_per_diagnosis']   = df_fe['num_medications'] / (df_fe['number_diagnoses'] + 1)

df_fe['has_weight']    = df_fe['weight'].notna().astype(int)
df_fe['has_specialty'] = df_fe['medical_specialty'].notna().astype(int)
df_fe['has_payer']     = df_fe['payer_code'].notna().astype(int)

df_fe.drop(columns=[
    'encounter_id', 'readmitted', 'weight', 'payer_code',
    'medical_specialty', 'diag_1', 'diag_2', 'diag_3', 'age'
], inplace=True)

# Cast categorical columns
cat_cols_list = df_fe.select_dtypes(include='object').columns.tolist()
for col in cat_cols_list:
    df_fe[col] = df_fe[col].astype('category')

print(f'      Features after engineering: {df_fe.shape[1] - 1}')
print(f'      Categorical columns: {len(cat_cols_list)}')

# ── 3. Data splitting ──────────────────────────────────────────────────────────

print('\n[3/6] Splitting data (patient-level GroupShuffleSplit)...')

X      = df_fe.drop(columns=['target'])
y      = df_fe['target']
groups = df_fe['patient_nbr']

gss1 = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
train_val_idx, test_idx = next(gss1.split(X, y, groups))

X_temp       = X.iloc[train_val_idx]
y_temp       = y.iloc[train_val_idx]
groups_temp  = groups.iloc[train_val_idx]
X_test       = X.iloc[test_idx].drop(columns=['patient_nbr'])
y_test       = y.iloc[test_idx]

gss2 = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
train_idx, val_idx = next(gss2.split(X_temp, y_temp, groups_temp))

X_train = X_temp.iloc[train_idx].drop(columns=['patient_nbr'])
y_train = y_temp.iloc[train_idx]
X_val   = X_temp.iloc[val_idx].drop(columns=['patient_nbr'])
y_val   = y_temp.iloc[val_idx]

scale_pos = (y_train == 0).sum() / (y_train == 1).sum()
print(f'      Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}')
print(f'      Features: {X_train.shape[1]} | scale_pos_weight: {scale_pos:.2f}')

# ── 4. Hyperparameter tuning (Optuna) ─────────────────────────────────────────

print('\n[4/6] Hyperparameter tuning — Optuna (50 trials)...')
print('      This takes ~5-10 minutes.')

def objective(trial):
    param = {
        'n_estimators':      1000,
        'learning_rate':     trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
        'max_depth':         trial.suggest_int('max_depth', 3, 8),
        'min_child_weight':  trial.suggest_int('min_child_weight', 1, 15),
        'subsample':         trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree':  trial.suggest_float('colsample_bytree', 0.4, 1.0),
        'gamma':             trial.suggest_float('gamma', 0, 5.0),
        'reg_alpha':         trial.suggest_float('reg_alpha', 1e-4, 10.0, log=True),
        'reg_lambda':        trial.suggest_float('reg_lambda', 1e-4, 10.0, log=True),
        'scale_pos_weight':  scale_pos,
        'enable_categorical': True,
        'tree_method':       'hist',
        'random_state':      42,
        'eval_metric':       'aucpr',
        'early_stopping_rounds': 30,
    }
    m = xgb.XGBClassifier(**param)
    m.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return average_precision_score(y_val, m.predict_proba(X_val)[:, 1])

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=50)
print(f'      Best AUPRC: {study.best_value:.4f}')

# ── 5. Train final model ───────────────────────────────────────────────────────

print('\n[5/6] Training final model...')

best_params = study.best_params.copy()
best_params.update({
    'n_estimators':       1000,
    'scale_pos_weight':   scale_pos,
    'enable_categorical': True,
    'tree_method':        'hist',
    'random_state':       42,
    'eval_metric':        'aucpr',
    'early_stopping_rounds': 50,
})

final_xgb = xgb.XGBClassifier(**best_params)
final_xgb.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
print(f'      Trees: {final_xgb.best_iteration} (early stopped)')

# Calibrated model for production predictions
cal_params = best_params.copy()
cal_params.pop('early_stopping_rounds')
cal_params['n_estimators'] = final_xgb.best_iteration

final_calibrated = CalibratedClassifierCV(
    estimator=xgb.XGBClassifier(**cal_params),
    method='isotonic', cv=3
)
final_calibrated.fit(X_train, y_train)

# Test metrics
y_test_proba = final_calibrated.predict_proba(X_test)[:, 1]
test_auroc   = roc_auc_score(y_test, y_test_proba)
test_auprc   = average_precision_score(y_test, y_test_proba)
test_brier   = brier_score_loss(y_test, y_test_proba)

# Bootstrap CIs
boot_auroc, boot_auprc = [], []
np.random.seed(42)
for i in range(1000):
    idx = resample(range(len(y_test)), random_state=i)
    yb, pb = y_test.iloc[idx], y_test_proba[idx]
    if len(yb.unique()) < 2: continue
    boot_auroc.append(roc_auc_score(yb, pb))
    boot_auprc.append(average_precision_score(yb, pb))

auroc_ci = np.percentile(boot_auroc, [2.5, 97.5])
auprc_ci = np.percentile(boot_auprc, [2.5, 97.5])

print(f'\n      ╔{"═"*48}╗')
print(f'      ║  TEST RESULTS                                  ║')
print(f'      ╠{"═"*48}╣')
print(f'      ║  AUROC: {test_auroc:.4f}  (95% CI: {auroc_ci[0]:.4f}–{auroc_ci[1]:.4f})  ║')
print(f'      ║  AUPRC: {test_auprc:.4f}  (95% CI: {auprc_ci[0]:.4f}–{auprc_ci[1]:.4f})  ║')
print(f'      ║  Brier: {test_brier:.4f}                               ║')
print(f'      ╚{"═"*48}╝')

# ── 6. Save model files ────────────────────────────────────────────────────────

print('\n[6/6] Saving model files...')

OUT_DIR = os.path.join(os.path.dirname(__file__), 'ml_models')
os.makedirs(OUT_DIR, exist_ok=True)

# Save uncalibrated model (SHAP requires XGBClassifier, not CalibratedClassifierCV)
joblib.dump(final_xgb,                os.path.join(OUT_DIR, 'xgboost_model.pkl'))
# Save calibrated model (used for actual predictions — better probability estimates)
joblib.dump(final_calibrated,         os.path.join(OUT_DIR, 'xgboost_calibrated_model.pkl'))
joblib.dump(X_train.columns.tolist(), os.path.join(OUT_DIR, 'feature_names.pkl'))
joblib.dump(cat_cols_list,            os.path.join(OUT_DIR, 'categorical_cols.pkl'))

print(f'      xgboost_model.pkl            saved  (uncalibrated — for SHAP)')
print(f'      xgboost_calibrated_model.pkl saved  (calibrated — for predictions)')
print(f'      feature_names.pkl            saved  ({X_train.shape[1]} features)')
print(f'      categorical_cols.pkl         saved  ({len(cat_cols_list)} categorical)')
print(f'\n      Output folder: {OUT_DIR}')
print('\n  Training complete! You can now start the ML service.')
print('=' * 60)
