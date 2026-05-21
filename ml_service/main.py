"""
FastAPI ML Microservice — Readmission Prediction
Runs on port 8001. Called by Django's /api/predict/ endpoint.

Preprocessing replicates the notebook pipeline exactly:
  - ICD-9 diagnosis grouping
  - Composite & interaction features
  - Native XGBoost categorical support (enable_categorical=True)
  - No one-hot encoding

Expects: POST /inference/ with patient clinical data (JSON)
Returns: { prediction, probability, shap_values }
"""

import os
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title='SmartHealthcare ML Service',
    description='XGBoost readmission prediction with SHAP explanations',
    version='2.0.0'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:8000', 'http://127.0.0.1:8000'],
    allow_methods=['POST'],
    allow_headers=['*'],
)

# ── Internal authentication ────────────────────────────────────────────────────

INTERNAL_SECRET = os.environ.get(
    'ML_SERVICE_SECRET_KEY',
    'smarthealthcare-internal-secret-2024'
)

def verify_internal_token(x_internal_token: str = Header(...)):
    """Reject any request that doesn't come with the correct internal secret."""
    if x_internal_token != INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail='Forbidden: invalid internal token.')

# ── Load model on startup ──────────────────────────────────────────────────────

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH    = os.path.join(BASE_DIR, 'ml_models', 'xgboost_model.pkl')
CAL_PATH      = os.path.join(BASE_DIR, 'ml_models', 'xgboost_calibrated_model.pkl')
FEAT_PATH     = os.path.join(BASE_DIR, 'ml_models', 'feature_names.pkl')
CAT_PATH      = os.path.join(BASE_DIR, 'ml_models', 'categorical_cols.pkl')

model           = None   # uncalibrated XGBClassifier — used only for SHAP
calibrated_model = None  # CalibratedClassifierCV — used for predictions
feature_names   = None
cat_cols        = None
booster         = None


@app.on_event('startup')
def load_model():
    global model, calibrated_model, feature_names, cat_cols, booster
    missing = [p for p in (MODEL_PATH, FEAT_PATH, CAT_PATH) if not os.path.exists(p)]
    if missing:
        for p in missing:
            print(f'WARNING: Missing file → {p}')
        print('Place model files in ml_models/ and restart.')
        return

    model         = joblib.load(MODEL_PATH)
    feature_names = joblib.load(FEAT_PATH)
    cat_cols      = joblib.load(CAT_PATH)
    booster       = model.get_booster()

    # Load calibrated model if available
    if os.path.exists(CAL_PATH):
        calibrated_model = joblib.load(CAL_PATH)
        print(f'Model loaded (calibrated + uncalibrated). Features: {len(feature_names)} | Categorical: {len(cat_cols)}')
    else:
        calibrated_model = model  # fallback to uncalibrated
        print(f'WARNING: Calibrated model not found — using uncalibrated for predictions.')
        print(f'Model loaded. Features: {len(feature_names)} | Categorical: {len(cat_cols)}')


# ── Input schema ───────────────────────────────────────────────────────────────

DIAG_CATEGORIES = ['diabetes', 'circulatory', 'respiratory', 'digestive',
                   'genitourinary', 'musculoskeletal', 'injury', 'neoplasms',
                   'external', 'other']

MED_STATUS = ['No', 'Steady', 'Up', 'Down']

class PatientData(BaseModel):
    # Demographics
    age:    str = '[50-60)'
    gender: str = 'Female'
    race:   str = 'Caucasian'

    # Admission details
    time_in_hospital:    int = 3
    num_lab_procedures:  int = 44
    num_procedures:      int = 1
    num_medications:     int = 16
    number_outpatient:   int = 0
    number_inpatient:    int = 0
    number_emergency:    int = 0
    number_diagnoses:    int = 9

    # Diagnosis categories (ICD-9 already grouped)
    diag_1_cat: str = 'other'
    diag_2_cat: str = 'other'
    diag_3_cat: str = 'other'

    # Lab results
    A1Cresult:    str = 'None'
    max_glu_serum: str = 'None'

    # Medications
    diabetesMed:  str = 'Yes'
    change:       str = 'No'
    insulin:      str = 'Steady'
    metformin:    str = 'No'
    repaglinide:  str = 'No'
    nateglinide:  str = 'No'
    chlorpropamide: str = 'No'
    glimepiride:  str = 'No'
    glipizide:    str = 'No'
    glyburide:    str = 'No'
    pioglitazone: str = 'No'
    rosiglitazone: str = 'No'
    acarbose:     str = 'No'

    # Administrative data availability flags (1 = recorded, 0 = missing)
    has_weight:    int = 0
    has_specialty: int = 0
    has_payer:     int = 0


# ── Feature engineering (mirrors notebook exactly) ────────────────────────────

AGE_MAP = {
    '[0-10)': 5,  '[10-20)': 15, '[20-30)': 25, '[30-40)': 35, '[40-50)': 45,
    '[50-60)': 55, '[60-70)': 65, '[70-80)': 75, '[80-90)': 85, '[90-100)': 95,
}

MED_COLS = [
    'metformin', 'repaglinide', 'nateglinide', 'chlorpropamide',
    'glimepiride', 'glipizide', 'glyburide', 'pioglitazone',
    'rosiglitazone', 'acarbose', 'insulin',
]


def build_feature_vector(data: PatientData) -> pd.DataFrame:
    """
    Replicates the notebook's preprocessing pipeline:
    1. Composite features (total_prior_visits, num_med_changes, etc.)
    2. Interaction features (age_x_medications, hospital_x_diagnoses, etc.)
    3. Missing-data flags (always 0 — web form never has weight/specialty/payer)
    4. Categorical dtype casting (same as notebook cell 7)
    5. Reindex to training feature set — fills unknown columns with NaN
    """
    row = {
        # Raw inputs
        'gender':            data.gender,
        'race':              data.race,
        'time_in_hospital':  data.time_in_hospital,
        'num_lab_procedures': data.num_lab_procedures,
        'num_procedures':    data.num_procedures,
        'num_medications':   data.num_medications,
        'number_outpatient': data.number_outpatient,
        'number_inpatient':  data.number_inpatient,
        'number_emergency':  data.number_emergency,
        'number_diagnoses':  data.number_diagnoses,
        'A1Cresult':         data.A1Cresult,
        'max_glu_serum':     data.max_glu_serum,
        'diabetesMed':       data.diabetesMed,
        'change':            data.change,
        'insulin':           data.insulin,
        'metformin':         data.metformin,
        'repaglinide':       data.repaglinide,
        'nateglinide':       data.nateglinide,
        'chlorpropamide':    data.chlorpropamide,
        'glimepiride':       data.glimepiride,
        'glipizide':         data.glipizide,
        'glyburide':         data.glyburide,
        'pioglitazone':      data.pioglitazone,
        'rosiglitazone':     data.rosiglitazone,
        'acarbose':          data.acarbose,
        # Diagnosis categories (pre-grouped, skipping ICD-9 map_diag)
        'diag_1_cat':        data.diag_1_cat,
        'diag_2_cat':        data.diag_2_cat,
        'diag_3_cat':        data.diag_3_cat,
    }

    df = pd.DataFrame([row])

    # ── Composite features ─────────────────────────────────────────────────────
    df['total_prior_visits'] = (
        df['number_outpatient'] + df['number_emergency'] + df['number_inpatient']
    )

    df['num_med_changes'] = sum(
        1 for col in MED_COLS
        if col in row and row[col] in ('Up', 'Down')
    )

    df['procedures_per_day'] = df['num_procedures'] / (df['time_in_hospital'] + 1)

    df['age_numeric'] = AGE_MAP.get(data.age, 55)  # default 55 if unrecognised

    # ── Interaction features ───────────────────────────────────────────────────
    df['age_x_medications']   = df['age_numeric'] * df['num_medications']
    df['hospital_x_diagnoses']= df['time_in_hospital'] * df['number_diagnoses']
    df['age_x_inpatient']     = df['age_numeric'] * df['number_inpatient']
    df['meds_per_diagnosis']  = df['num_medications'] / (df['number_diagnoses'] + 1)

    # ── Missing-data flags (provided by the user via the form) ───────────────
    df['has_weight']    = int(data.has_weight)
    df['has_specialty'] = int(data.has_specialty)
    df['has_payer']     = int(data.has_payer)

    # ── Cast categorical columns (same as notebook cell 7) ────────────────────
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype('category')

    # ── Align to training feature set ─────────────────────────────────────────
    df = df.reindex(columns=feature_names)

    # For categorical columns XGBoost requires the dtype to match training.
    # - Has a value → already cast to category before reindex, keep it.
    # - All NaN after reindex (column not in form input) → create a Categorical
    #   with a string placeholder category so XGBoost sees string-based codes
    #   (not float). The value stays NaN (code = -1), treated as missing.
    for col in cat_cols:
        if col in df.columns and df[col].dtype.name != 'category':
            if df[col].isna().all():
                df[col] = pd.Categorical([None] * len(df), categories=['No'])
            else:
                df[col] = df[col].astype('category')

    return df


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get('/')
def health():
    return {
        'status': 'ok',
        'model_loaded': model is not None,
        'features': len(feature_names) if feature_names else 0,
    }


@app.post('/inference/', dependencies=[Depends(verify_internal_token)])
def inference(data: PatientData):
    if model is None or feature_names is None:
        raise HTTPException(
            status_code=503,
            detail='ML model is not loaded. Run the notebook save cell first and place '
                   'xgboost_model.pkl, feature_names.pkl, categorical_cols.pkl in ml_models/'
        )

    X = build_feature_vector(data)

    # Predict using calibrated model (better probability estimates)
    probability = float(calibrated_model.predict_proba(X)[0][1])
    prediction  = probability >= 0.5

    # SHAP values via XGBoost native pred_contribs (no shap package required)
    # Categorical columns must be converted to numeric codes before passing to DMatrix
    shap_values = None
    try:
        X_shap = X.copy()
        for col in X_shap.select_dtypes(include='category').columns:
            X_shap[col] = X_shap[col].cat.codes.astype(float).replace(-1.0, np.nan)
        dmatrix    = xgb.DMatrix(X_shap)
        sv         = booster.predict(dmatrix, pred_contribs=True)
        shap_array = sv[0][:-1]  # last column is the bias term — exclude it
        shap_values = [
            {'feature': str(feat), 'value': float(val)}
            for feat, val in zip(feature_names, shap_array)
            if abs(val) > 0.0001
        ]
        shap_values = sorted(shap_values, key=lambda x: abs(x['value']), reverse=True)[:30]
    except Exception as e:
        print(f'SHAP computation failed: {e}')

    return {
        'prediction':  prediction,
        'probability': round(probability, 6),
        'shap_values': shap_values,
    }
