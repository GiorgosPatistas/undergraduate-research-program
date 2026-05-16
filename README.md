# Smart Healthcare System — Hospital Readmission Prediction

**Undergraduate Thesis**
**Dataset:** Diabetes 130-US Hospitals 1999–2008 (Kaggle)
**Primary Model:** XGBoost with probability calibration (AUROC ≈ 0.67)

---

## System Overview

The project consists of three independently running services:

| Service | Technology | Port |
|---|---|---|
| ML Inference | FastAPI + XGBoost | 8001 |
| REST API | Django 4.2 + DRF | 8000 |
| Frontend | Vue 3 + Vite | 5173 |

Django calls the FastAPI service internally. The two services communicate using a shared secret key — the FastAPI service rejects any request that does not include the correct `X-Internal-Token` header.

The Django backend also ships with a **custom admin dashboard** (at `/admin/`) that extends the default Django admin with an analytics view: aggregate KPIs, trend charts (Chart.js), and recent activity tables — on top of the standard CRUD interface for every model.

---

## Prerequisites

- **Python 3.10–3.13** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **npm** (comes with Node.js)

> **⚠ Important:** Python **3.14 is not supported** — it breaks Django 4.2 template rendering (`AttributeError: 'super' object has no attribute 'dicts'` on admin add/change views). If you have multiple Python versions installed, use `py -3.13 -m venv venv` to create a virtual environment with Python 3.13 and activate it before running any `pip install` or `python manage.py` command.

---

## One-Time Setup

### 1. Train and save the ML models

Before starting any service for the first time, generate the model files by running the training script from inside the `ml_service/` directory:

```bash
cd ml_service
pip install -r requirements.txt
python train_and_save.py
```

This produces four files inside `ml_service/ml_models/`:

```
ml_models/
├── xgboost_model.pkl            # Raw XGBoost classifier (used for SHAP)
├── xgboost_calibrated_model.pkl # Probability-calibrated wrapper (used for predictions)
├── feature_names.pkl            # Ordered list of training features
└── categorical_cols.pkl         # Column names that require categorical dtype
```

You only need to run this once. The model files persist between restarts.

### 2. Configure environment variables

Copy the example file and set the shared secret key:

```bash
cd backend
cp .env.example .env
```

Open `.env` and set a strong value for `ML_SERVICE_SECRET_KEY`. The same key is read automatically by both Django and FastAPI, so you only need to change it in one place.

### 3. Install backend dependencies and apply migrations

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
```

### 4. Create an admin superuser

Required to log into the admin dashboard at `/admin/`:

```bash
cd backend
python manage.py createsuperuser
```

You will be prompted for a `username`, `email`, and `password`. Remember the **username** — that is what you log in with at `/admin/` (not the email).

### 5. Install frontend dependencies

```bash
cd frontend
npm install
```

---

## Startup Instructions

Open **3 separate terminals** and start the services in the order below.

> **Important:** Always start ML Service first, then Django, then Vue. Django calls FastAPI immediately on the first prediction request, so FastAPI must already be running.

---

### Terminal 1 — ML Service (FastAPI · port 8001)

```bash
cd ml_service
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Expected output:**
```
Model loaded (calibrated + uncalibrated). Features: 54 | Categorical: 32
INFO: Uvicorn running on http://0.0.0.0:8001
```

Health check: `http://localhost:8001/`
Expected: `{"status": "ok", "model_loaded": true, "features": 54}`

---

### Terminal 2 — Backend (Django · port 8000)

```bash
cd backend
python manage.py runserver
```

**Expected output:**
```
Django version 4.2.x
Starting development server at http://127.0.0.1:8000/
```

Admin panel + dashboard: `http://localhost:8000/admin/` (log in with the superuser created in setup step 4).

---

### Terminal 3 — Frontend (Vue 3 · port 5173)

```bash
cd frontend
npm install
npm run dev
```

**Expected output:**
```
VITE ready in ... ms
Local: http://localhost:5173/
```

Open `http://localhost:5173` in your browser.

---

## Using the Application

### Patient / Doctor workflow (Vue frontend at :5173)

1. **Register** a new account — choose *Patient* or *Doctor* during registration.
2. **Log in** with your credentials.
3. As a **Patient**: go to the Services page, fill in the clinical form, and submit to receive a readmission risk prediction with a SHAP explanation of the top contributing factors.
4. As a **Doctor**: view your scheduled patient appointments and publish articles on the Blog page.

### Admin dashboard (Django at :8000/admin/)

Log in with the **superuser** created during setup. The dashboard is split into two layers:

**Top — custom analytics dashboard** (read-only overview of the whole system)
- **Key Metrics** cards: total users (with patient/doctor split & week-over-week delta), total predictions, high-risk rate (with visual progress bar), appointments (with confirmation rate bar).
- **Secondary Metrics** strip: predictions this week, confirmation rate, article count, upvote rate.
- **Trends & Distribution** charts (Chart.js): predictions volume over the last 30 days (gradient line), risk distribution (doughnut), appointments by status (bar), users by role (pie), top 5 doctors by appointments (horizontal bar).
- **Recent Activity** tables: 5 most recent predictions and appointments with status pills.

**Bottom — standard Django admin CRUD**
- `ACCOUNTS → Users`: manage every user account (role, staff status, password reset).
- `API → Predictions`: every prediction ever made, including the full clinical `input_data` and `shap_values` JSON (useful for audit & debugging).
- `API → Appointments`, `Articles`, `Votes`: full CRUD on all business data.
- `AUTHENTICATION AND AUTHORIZATION → Groups`: Django's built-in RBAC (not used actively — role-based access is handled by the custom `role` field on `User` and permission classes in `api/permissions.py`).

---

## Running the Tests

Tests cover both the `accounts` app (auth flows) and the `api` app (predictions, appointments, blog, votes).

```bash
cd backend
python manage.py test
```

**Expected output:**
```
..............................................
----------------------------------------------------------------------
Ran 43 tests in X.XXXs

OK
```

---

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | None | Register a new account |
| POST | `/api/auth/login/` | None | Obtain JWT access + refresh tokens |
| POST | `/api/auth/refresh/` | None | Refresh access token |
| GET | `/api/auth/me/` | Bearer | Get own profile |
| PATCH | `/api/auth/me/` | Bearer | Update profile |
| POST | `/api/auth/change-password/` | Bearer | Change password |
| GET | `/api/auth/doctors/` | Bearer | List all doctors |
| POST | `/api/predict/` | Bearer (Patient) | Run readmission prediction |
| GET | `/api/predictions/` | Bearer (Patient) | View prediction history |
| GET | `/api/appointments/` | Bearer | List appointments |
| POST | `/api/appointments/` | Bearer (Patient) | Book an appointment |
| PATCH | `/api/appointments/<id>/status/` | Bearer | Confirm or cancel an appointment |
| GET | `/api/blog/` | Bearer | List articles (paginated) |
| POST | `/api/blog/` | Bearer (Doctor) | Publish an article |
| POST | `/api/blog/<id>/vote/` | Bearer (Patient) | Cast a vote (upvote / downvote) |
| PATCH | `/api/blog/<id>/vote/` | Bearer (Patient) | Change an existing vote |
| DELETE | `/api/blog/<id>/vote/` | Bearer (Patient) | Remove a vote |

---

## Project Structure

```
.
├── ml_service/                  # FastAPI ML microservice
│   ├── main.py                  # FastAPI app, preprocessing pipeline, inference endpoint
│   ├── train_and_save.py        # Trains XGBoost, calibrates, saves all model files
│   ├── ml_models/               # Generated model files (git-ignored)
│   │   ├── xgboost_model.pkl
│   │   ├── xgboost_calibrated_model.pkl
│   │   ├── feature_names.pkl
│   │   └── categorical_cols.pkl
│   └── requirements.txt
│
├── backend/                     # Django REST API
│   ├── accounts/                # Custom user model (Patient / Doctor roles)
│   │   └── tests.py             # Auth test suite (register, login, profile, password)
│   ├── api/                     # Predictions, Appointments, Blog endpoints
│   │   └── tests.py             # API test suite (predict, appointments, blog, votes)
│   ├── core/                    # Django settings & URL routing
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── admin_dashboard.py   # Custom admin dashboard (KPIs, charts, activity)
│   ├── templates/
│   │   └── admin/
│   │       └── index.html       # Dashboard template (Chart.js, CSS, dark-mode aware)
│   ├── .env                     # Local environment variables (git-ignored)
│   ├── .env.example             # Template for environment variables
│   └── requirements.txt
│
└── frontend/                    # Vue 3 + Vite frontend
    ├── src/
    │   ├── views/               # Page components (Home, Login, Services, Blog…)
    │   ├── stores/              # Pinia state management
    │   └── services/            # Axios API client
    └── package.json
```

---

## ML Pipeline Notes

**Model:** XGBoost trained on the Diabetes 130-US Hospitals dataset with native categorical support (`enable_categorical=True`). Probabilities are refined using `CalibratedClassifierCV` (isotonic regression).

**Predictions** use the calibrated model for better-calibrated probabilities. **SHAP explanations** use the raw XGBoost booster via `TreeExplainer`, since calibration wrappers are not directly compatible with SHAP.

**Feature engineering** mirrors the notebook preprocessing exactly:
- ICD-9 diagnosis codes grouped into 10 clinical categories
- Composite features: `total_prior_visits`, `num_med_changes`, `procedures_per_day`
- Interaction features: `age_x_medications`, `hospital_x_diagnoses`, `age_x_inpatient`, `meds_per_diagnosis`
- Missing-data flags: `has_weight`, `has_specialty`, `has_payer` — these are passed from the clinical form to reflect whether administrative data was recorded (MNAR informative missingness)

---

## Troubleshooting

**`AttributeError: 'super' object has no attribute 'dicts'` on admin pages**
You are running Python 3.14, which is incompatible with Django 4.2 template rendering. Create a virtual environment with Python 3.13:
```bash
cd backend
py -3.13 -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # macOS / Linux
pip install -r requirements.txt
```
Do the same inside `ml_service/`. Activate the venv (`venv\Scripts\activate`) in every terminal before running `runserver` / `uvicorn`.

**Admin login fails with "Please enter the correct username and password for a staff account"**
The `/admin/` login expects the **username** you chose in `createsuperuser`, not an email, and the account must have `is_staff=True`. Accounts registered through the frontend form are regular users (patient/doctor) and cannot log in to `/admin/`. Either create a superuser (`python manage.py createsuperuser`) or promote an existing account:
```bash
python manage.py shell
>>> from accounts.models import User
>>> u = User.objects.get(email='your@email.com')
>>> u.is_staff = True; u.is_superuser = True; u.save()
```

**Dashboard charts are blank boxes**
The browser could not load Chart.js from the CDN. Check your internet connection or ad-blocker — the template fetches `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/...`.

**`TemplateDoesNotExist: admin/index.html`**
Make sure `backend/templates/admin/index.html` exists and that `backend/core/settings.py` has `'DIRS': [BASE_DIR / 'templates']` inside the `TEMPLATES` setting.

**"ML model is not loaded"**
Run `python train_and_save.py` inside `ml_service/` to generate the model files, then restart uvicorn.

**"Forbidden: invalid internal token"**
The `ML_SERVICE_SECRET_KEY` in `backend/.env` does not match the value in `ml_service/` environment. Ensure both services use the same key (Django reads from `.env`, FastAPI from the `ML_SERVICE_SECRET_KEY` environment variable or its default).

**CORS error in browser**
The frontend must run on `http://localhost:5173`. If you change the port, update `CORS_ALLOWED_ORIGINS` in `backend/core/settings.py` and `allow_origins` in `ml_service/main.py`.

**`ModuleNotFoundError` on startup**
Run `pip install -r requirements.txt` inside the correct directory (`ml_service/` or `backend/`) before starting the service.

**Port already in use**
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# macOS / Linux
lsof -ti:8001 | xargs kill
lsof -ti:8000 | xargs kill
```
