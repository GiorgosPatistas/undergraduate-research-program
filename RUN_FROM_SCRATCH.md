# Πώς να τρέξεις το project από την αρχή

Οδηγός βήμα-βήμα για να στήσεις και να τρέξεις το Smart Healthcare System
(ML service + Django backend + Vue frontend), συμπεριλαμβανομένου του
νέου custom admin dashboard.

---

## 0. Προαπαιτούμενα

Έλεγξε ότι έχεις εγκατεστημένα:

- **Python 3.10–3.13** (όχι 3.14 — ασυμβατότητα με Django 4.x)
- **Node.js 18+** (περιλαμβάνει npm)
- Git (προαιρετικό)

Σε PowerShell / cmd:

```bash
python --version
node --version
npm --version
```

---

## 1. Εκπαίδευση μοντέλου ML (μόνο μια φορά)

Από τον root φάκελο του project:

```bash
cd ml_service
pip install -r requirements.txt
python train_and_save.py
```

Αυτό παράγει 4 αρχεία στο `ml_service/ml_models/`:

- `xgboost_model.pkl`
- `xgboost_calibrated_model.pkl`
- `feature_names.pkl`
- `categorical_cols.pkl`

Αυτό το βήμα το τρέχεις **μόνο την πρώτη φορά** — μετά τα αρχεία
παραμένουν και δεν χρειάζεται να ξανατρέξεις το training.

---

## 2. Ρύθμιση environment variables (μόνο μια φορά)

```bash
cd backend
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
```

Άνοιξε το `backend/.env` και βάλε έναν ισχυρό τυχαίο string στο
`ML_SERVICE_SECRET_KEY`. Η ίδια τιμή διαβάζεται αυτόματα και από το
FastAPI, άρα αλλάζεις μία φορά.

---

## 3. Εγκατάσταση Django dependencies & migrations (μόνο μια φορά)

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
```

---

## 4. Δημιουργία superuser για το admin dashboard

Αυτό είναι **καινούριο βήμα** — είναι ο χρήστης που θα βλέπει το
dashboard με όλα τα στατιστικά (το custom admin που φτιάξαμε).

```bash
cd backend
python manage.py createsuperuser
```

Θα σου ζητήσει:
- `Username` (π.χ. `admin`)
- `Email` (μπορείς να βάλεις ό,τι θες)
- `Password` (τουλάχιστον 8 χαρακτήρες)

Κράτα κάπου username και password — αυτά θα βάζεις στο login του admin.

---

## 5. Εγκατάσταση Vue dependencies (μόνο μια φορά)

```bash
cd frontend
npm install
```

---

## 6. Τρέξιμο της εφαρμογής (κάθε φορά που την ξεκινάς)

**Χρειάζεσαι 3 ξεχωριστά terminals.** Τα ανοίγεις με τη σειρά:

### Terminal 1 — ML Service (FastAPI, port 8001)

```bash
cd ml_service
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Περιμένεις να δεις:
```
Model loaded (calibrated + uncalibrated). Features: 54 | Categorical: 32
INFO: Uvicorn running on http://0.0.0.0:8001
```

### Terminal 2 — Django Backend (port 8000)

```bash
cd backend
python manage.py runserver
```

Περιμένεις:
```
Starting development server at http://127.0.0.1:8000/
```

### Terminal 3 — Vue Frontend (port 5173)

```bash
cd frontend
npm run dev
```

Περιμένεις:
```
Local: http://localhost:5173/
```

---

## 7. Πού πάω για τι

| Τι θες να δεις | URL | Login |
|---|---|---|
| Κανονική εφαρμογή (ασθενείς / γιατροί) | `http://localhost:5173` | Register patient ή doctor από το UI |
| **Admin dashboard με στατιστικά** | `http://localhost:8000/admin/` | **Superuser** που έφτιαξες στο βήμα 4 |
| ML service health check | `http://localhost:8001/` | — |

---

## 8. Τι θα δεις στο admin dashboard

Το `/admin/` πλέον εμφανίζει **πάνω από το standard Django admin**:

- **5 stat cards** — users (ανά ρόλο), predictions (με μέσο probability),
  % high risk, appointments (με status breakdown), articles (με votes)
- **5 γραφήματα** (Chart.js):
  - Predictions τελευταίες 30 ημέρες (line)
  - Risk distribution high vs low (doughnut)
  - Appointments ανά status (bar)
  - Users ανά ρόλο (pie)
  - Top 5 γιατροί κατά αριθμό ραντεβού (horizontal bar)
- **2 πίνακες recent activity** — τα 5 τελευταία predictions και
  appointments

Κάτω από αυτά βλέπεις τη standard Django admin λίστα (Users,
Predictions, Appointments, Articles, Votes) που μπορείς να
browse/edit/delete.

---

## 9. Troubleshooting (συχνά προβλήματα)

**Το dashboard δεν εμφανίζει γραφήματα, μόνο κενά κουτιά.**
Ο browser δεν μπορεί να φορτώσει το Chart.js από CDN. Έλεγξε σύνδεση
στο internet, ή «Disable adblock» αν έχεις.

**`TemplateDoesNotExist: admin/index.html`.**
Σιγουρέψου ότι υπάρχει ο φάκελος `backend/templates/admin/` και μέσα το
`index.html`. Επίσης ότι το `settings.py` έχει:
```python
'DIRS': [BASE_DIR / 'templates'],
```

**`"ML model is not loaded"` στο Django.**
Ξανατρέξε `python train_and_save.py` μέσα στο `ml_service/`.

**`"Forbidden: invalid internal token"`.**
Το `ML_SERVICE_SECRET_KEY` στο `backend/.env` δεν ταιριάζει. Σιγουρέψου
ότι είναι το ίδιο key και στα δύο services (αν τρέχεις ξεχωριστά το
FastAPI πρέπει να περάσεις το key ως env var).

**Port already in use.**
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

**`Login failed` στο admin.**
Ξαναδημιούργησε superuser: `python manage.py createsuperuser`.

---

## 10. Quick restart (όταν έχεις ήδη τα πάντα στημένα)

Αν έχεις ήδη τρέξει όλα τα setup βήματα (1–5), κάθε επόμενη φορά
χρειάζεσαι **μόνο** τα 3 terminals του βήματος 6.
