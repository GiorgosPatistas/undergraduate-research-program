# Smart Healthcare — Startup Guide

This guide explains how to run all three parts of the project locally:
**Frontend** (Vue 3 / Vite), **Backend** (Django), and **ML Service** (FastAPI).

You need **3 separate terminals** open at the same time.

---

## Prerequisites

- Python 3.10+ and `pip`
- Node.js 18+ and `npm`
- The trained model files: `xgboost_model.pkl` and `feature_names.pkl`

---

## 1 — ML Service (FastAPI · port 8001)

```bash
cd ml_service

# First time only
pip install -r requirements.txt

# Place your model files before starting:
#   ml_service/ml_models/xgboost_model.pkl
#   ml_service/ml_models/feature_names.pkl

uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Visit `http://localhost:8001/` — you should see `{"status":"ok","model_loaded":true}`.

---

## 2 — Backend (Django · port 8000)

```bash
cd backend

# First time only
pip install -r requirements.txt

# Copy the example env file and fill in your values
cp .env.example .env
# Edit .env — at minimum set a SECRET_KEY, e.g.:
# SECRET_KEY=django-insecure-change-me-in-production

# Create the database tables
python manage.py makemigrations accounts api
python manage.py migrate

# (Optional) Create a superuser for the Django admin
python manage.py createsuperuser

# Start the server
python manage.py runserver
```

Django admin is at `http://localhost:8000/admin/`.

---

## 3 — Frontend (Vue 3 / Vite · port 5173)

```bash
cd frontend

# First time only
npm install

npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Startup order

Always start the services in this order:

```
1. ML Service  →  2. Django  →  3. Vue
```

Vue talks to Django via the `/api` Vite proxy.
Django talks to FastAPI directly at `http://localhost:8001`.

---

## Environment variables (backend/.env)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(required)* | Django secret key |
| `DEBUG` | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Vue dev server origin |
| `ML_SERVICE_URL` | `http://localhost:8001` | FastAPI microservice URL |

---

## Quick API reference

| Method | URL | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register/` | None | Register (patient or doctor) |
| `POST` | `/api/auth/login/` | None | Get JWT access + refresh tokens |
| `POST` | `/api/auth/refresh/` | None | Refresh access token |
| `GET` | `/api/auth/me/` | Bearer | Get own profile |
| `PATCH` | `/api/auth/me/` | Bearer | Update profile |
| `POST` | `/api/auth/change-password/` | Bearer | Change password |
| `GET` | `/api/auth/doctors/` | Bearer | List all doctors |
| `POST` | `/api/predict/` | Bearer (patient) | Run readmission prediction |
| `GET` | `/api/appointments/` | Bearer | List appointments |
| `POST` | `/api/appointments/` | Bearer (patient) | Book appointment |
| `GET` | `/api/blog/` | Bearer | List articles |
| `POST` | `/api/blog/` | Bearer (doctor) | Publish article |
| `POST` | `/api/blog/<id>/vote/` | Bearer (patient) | Upvote / downvote article |

---

## Common issues

**"ML model is not loaded"** — Make sure `xgboost_model.pkl` and `feature_names.pkl` are placed inside `ml_service/ml_models/` before starting uvicorn.

**CORS error in browser** — Check that `CORS_ALLOWED_ORIGINS` in `backend/.env` includes `http://localhost:5173`.

**`ModuleNotFoundError`** — You may be running Python from the wrong virtual environment. Always activate your venv before running `pip install` or `python manage.py`.
