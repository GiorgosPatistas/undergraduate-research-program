# Smart Healthcare System — Integration of Ai technologies in medical practice

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

---

## Prerequisites

Before you begin, make sure the following are installed on your system:

- **Python 3.10–3.13** — [python.org](https://www.python.org/downloads/)  
  ⚠️ **Python 3.14 is not supported** — it breaks Django 4.2 template rendering.
- **Node.js 18+** — [nodejs.org](https://nodejs.org/) (includes npm)
- **Git** — [git-scm.com](https://git-scm.com/)

Verify your versions in a terminal:

```bash
python --version
node --version
npm --version
```

---

## 1. Clone the Repository

```bash
git clone https://github.com/GiorgosPatistas/undergraduate-research-program.git
cd undergraduate-research-program
```

---

## 2. One-Time Setup

Run these steps once when you first set up the project. You do not need to repeat them on subsequent runs.

### 2.1 Set up Python virtual environments

The project uses two separate virtual environments — one for the ML service and one for the Django backend. You must activate the correct one in each terminal before running any Python command.

**ML Service venv:**

```bash
cd ml_service

# Create the virtual environment (first time only)
python -m venv venv

# Activate it — Windows
venv\Scripts\activate

# Activate it — macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
```

**Backend venv:**

```bash
cd backend

# Create the virtual environment (first time only)
python -m venv venv

# Activate it — Windows
venv\Scripts\activate

# Activate it — macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
```

> ⚠️ **Important:** You must activate the virtual environment every time you open a new terminal before running `uvicorn` or `python manage.py`. If you forget, you will get `ModuleNotFoundError`.

---

### 2.2 Train and save the ML model

With the `ml_service` venv active, first install the extra dependency needed only for training:

```bash
cd ml_service
venv\Scripts\activate      # if not already active

pip install optuna
python train_and_save.py
```

> **Note:** `optuna` is only needed to run `train_and_save.py`. It is not required to start the ML service (`uvicorn`).

This generates four files inside `ml_service/ml_models/`:

```
ml_models/
├── xgboost_model.pkl
├── xgboost_calibrated_model.pkl
├── feature_names.pkl
└── categorical_cols.pkl
```

You only need to run this once. The model files persist between restarts.

---

### 2.3 Configure environment variables

```bash
cd backend
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
```

Open `backend/.env` and set a strong random value for `ML_SERVICE_SECRET_KEY`. The same key is read automatically by both Django and FastAPI, so you only need to set it in one place.

```env
SECRET_KEY=django-insecure-change-me-in-production-please
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ML_SERVICE_URL=http://localhost:8001
ML_SERVICE_SECRET_KEY=replace-this-with-a-strong-random-secret
```

---

### 2.4 Apply database migrations

With the `backend` venv active:

```bash
cd backend
venv\Scripts\activate      # if not already active

python manage.py migrate
```

---

### 2.5 Create an admin superuser

Required to access the Django admin dashboard at `/admin/`:

```bash
cd backend
python manage.py createsuperuser
```

You will be prompted for a username, email, and password. Use the **username** (not email) to log in at `http://localhost:8000/admin/`.

---

### 2.6 Install frontend dependencies

```bash
cd frontend
npm install
```

---

## 3. Running the Application

Every time you want to start the project, open **3 separate terminals** and start the services in the order below. Always start the ML service first, then Django, then Vue.

---

### Terminal 1 — ML Service (FastAPI · port 8001)

```bash
cd ml_service
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Wait until you see:

```
Model loaded (calibrated + uncalibrated). Features: 54 | Categorical: 32
INFO: Uvicorn running on http://0.0.0.0:8001
```

Health check: open `http://localhost:8001/` — you should get `{"status":"ok","model_loaded":true}`.

---

### Terminal 2 — Backend (Django · port 8000)

```bash
cd backend
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

python manage.py runserver
```

Wait until you see:

```
Django version 4.2.x
Starting development server at http://127.0.0.1:8000/
```

---

### Terminal 3 — Frontend (Vue 3 · port 5173)

```bash
cd frontend
npm run dev
```

Wait until you see:

```
VITE ready in ... ms
Local: http://localhost:5173/
```

Open `http://localhost:5173` in your browser.

---

## 4. Where to Go

| What | URL | Login |
|---|---|---|
| Main application (patients / doctors) | `http://localhost:5173` | Register as patient or doctor from the UI |
| Admin dashboard | `http://localhost:8000/admin/` | Superuser created in step 2.5 |
| ML service health check | `http://localhost:8001/` | — |

---

## 5. API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | None | Register a new account |
| POST | `/api/auth/login/` | None | Obtain JWT access + refresh tokens |
| POST | `/api/auth/refresh/` | None | Refresh access token |
| GET | `/api/auth/me/` | Bearer | Get own profile |
| PATCH | `/api/auth/me/` | Bearer | Update profile |
| POST | `/api/auth/change-password/` | Bearer | Change password |
| GET | `/api/auth/doctors/` | Bearer | List all doctors |
| POST | `/api/predict/` | Bearer (Patient or Doctor) | Run readmission prediction |
| GET | `/api/predictions/` | Bearer (Patient) | View prediction history |
| GET | `/api/appointments/` | Bearer | List appointments |
| POST | `/api/appointments/` | Bearer (Patient) | Book an appointment |
| PATCH | `/api/appointments/<id>/status/` | Bearer | Confirm or cancel an appointment |
| GET | `/api/blog/` | Bearer | List articles |
| POST | `/api/blog/` | Bearer (Doctor) | Publish an article |
| POST | `/api/blog/<id>/vote/` | Bearer (Patient) | Cast a vote |
| PATCH | `/api/blog/<id>/vote/` | Bearer (Patient) | Change a vote |
| DELETE | `/api/blog/<id>/vote/` | Bearer (Patient) | Remove a vote |

---

## 6. Project Structure

```
.
├── ml_service/                  # FastAPI ML microservice
│   ├── main.py                  # FastAPI app, preprocessing pipeline, inference endpoint
│   ├── train_and_save.py        # Trains XGBoost, calibrates, saves all model files
│   ├── ml_models/               # Generated model files (git-ignored)
│   └── requirements.txt
│
├── backend/                     # Django REST API
│   ├── accounts/                # Custom user model (Patient / Doctor roles)
│   ├── api/                     # Predictions, Appointments, Blog endpoints
│   ├── core/                    # Django settings, URL routing, admin dashboard
│   ├── templates/admin/         # Custom admin dashboard template (Chart.js)
│   ├── .env                     # Local environment variables (git-ignored)
│   ├── .env.example             # Template for environment variables
│   └── requirements.txt
│
└── frontend/                    # Vue 3 + Vite frontend
    ├── src/
    │   ├── views/               # Page components
    │   ├── stores/              # Pinia state management
    │   └── services/            # Axios API client
    └── package.json
```

---

## 7. Running the Tests

```bash
cd backend
venv\Scripts\activate
python manage.py test
```

Expected output:

```
..............................................
----------------------------------------------------------------------
Ran 43 tests in X.XXXs

OK
```

---

## 8. Troubleshooting

**`ModuleNotFoundError` on startup**  
You forgot to activate the virtual environment. Run `venv\Scripts\activate` inside `ml_service/` or `backend/` before starting the service.

**`AttributeError: 'super' object has no attribute 'dicts'` on admin pages**  
You are running Python 3.14, which is incompatible with Django 4.2. Recreate the venv using Python 3.13:
```bash
py -3.13 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**`"ML model is not loaded"`**  
Run `python train_and_save.py` inside `ml_service/` to generate the model files, then restart uvicorn.

**`"Forbidden: invalid internal token"`**  
The `ML_SERVICE_SECRET_KEY` in `backend/.env` does not match the key FastAPI is using. Make sure both services share the same value.

**CORS error in browser**  
The frontend must run on `http://localhost:5173`. If you change the port, update `CORS_ALLOWED_ORIGINS` in `backend/.env` and `allow_origins` in `ml_service/main.py`.

**Admin login fails**  
The `/admin/` login requires the **username** you set in `createsuperuser`, not an email. Regular frontend accounts (patient/doctor) cannot log in to `/admin/`.

**Port already in use**  
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

**Dashboard charts are blank**  
The browser could not load Chart.js from the CDN. Check your internet connection or disable your ad-blocker.
