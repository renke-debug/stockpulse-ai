# StockPulse AI - Deployment Guide

## Snelle start (15 minuten)

### Stap 1: GitHub repository aanmaken

```bash
cd stockpulse-ai
git init
git add .
git commit -m "Initial commit: StockPulse AI with verification system"
```

Ga naar https://github.com/new en maak een nieuwe repository aan.

```bash
git remote add origin https://github.com/JOUW_USERNAME/stockpulse-ai.git
git branch -M main
git push -u origin main
```

---

### Stap 2: Backend deployen op Railway

1. Ga naar https://railway.app en log in met GitHub
2. Klik **"New Project"** → **"Deploy from GitHub repo"**
3. Selecteer je `stockpulse-ai` repository
4. Railway detecteert automatisch de backend folder

**Configureer de service:**
- Klik op de service → **Settings** → **Root Directory**: `backend`
- Ga naar **Variables** en voeg toe:

```
DATABASE_URL=sqlite:///./stockpulse.db
SECRET_KEY=genereer-een-random-string-van-32-tekens
APP_NAME=StockPulse AI
```

**Start command instellen:**
- Settings → Deploy → Custom Start Command:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Wacht tot deployment klaar is
6. Kopieer de URL (bijv: `https://stockpulse-ai-production.up.railway.app`)

---

### Stap 3: Frontend deployen op Vercel

1. Ga naar https://vercel.com en log in met GitHub
2. Klik **"Add New Project"** → Import je `stockpulse-ai` repo
3. Configureer:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js (auto-detected)

4. Voeg Environment Variable toe:
```
NEXT_PUBLIC_API_URL=https://JOUW-RAILWAY-URL.up.railway.app
```

5. Klik **Deploy**
6. Na ~2 minuten is je frontend live!

---

### Stap 4: CORS updaten op Railway

Ga terug naar Railway en voeg in Variables toe:
```
ALLOWED_ORIGINS=https://jouw-app.vercel.app,http://localhost:3000
```

---

### Stap 5: Database initialiseren

In Railway, ga naar je service en open **"Deploy Logs"** of gebruik de Railway CLI:

```bash
railway run python -c "from app.models.database import init_db; init_db(); print('DB initialized')"
```

Of voeg een startup script toe aan `backend/app/main.py` (zie hieronder).

---

## Automatische database init (aanbevolen)

Voeg dit toe aan `backend/app/main.py` na de imports:

```python
from app.models.database import init_db

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
```

---

## GitHub Actions voor dagelijkse digest

De workflow staat al klaar in `.github/workflows/daily-digest.yml`.

Voeg deze secrets toe aan je GitHub repo (Settings → Secrets → Actions):

```
RAILWAY_TOKEN=<krijg je via railway login>
DATABASE_URL=<zelfde als in Railway>
```

---

## Testen

1. Open je Vercel URL
2. Maak een account aan met budget
3. Genereer je eerste digest (kan even duren, haalt live data op)
4. Check de verificatie pagina - staat in observatiemodus

---

## Troubleshooting

**Backend start niet:**
- Check of `requirements.txt` volledig is
- Voeg eventueel toe: `email-validator`

**CORS errors:**
- Voeg je Vercel URL toe aan ALLOWED_ORIGINS in Railway

**Database errors:**
- Zorg dat `init_db()` wordt aangeroepen bij startup

---

## Kosten

- **Railway**: Gratis tier = $5/maand credits (meer dan genoeg)
- **Vercel**: Gratis voor hobby projecten
- **Data APIs**: Allemaal gratis (Yahoo Finance, RSS feeds)

Totaal: **€0/maand** voor persoonlijk gebruik
