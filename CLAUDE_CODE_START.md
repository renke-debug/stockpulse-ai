# StockPulse AI - Snelstart voor Claude Code (terminal)

Open Claude Code in je terminal en plak onderstaande commando's.

## 1. Navigeer naar project

```bash
cd ~/path/to/stockpulse-ai  # pas aan naar jouw locatie
```

## 2. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Start backend (laat draaien in aparte terminal)

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 4. Frontend setup (nieuwe terminal)

```bash
cd frontend
npm install
```

## 5. Start frontend

```bash
cd frontend
npm run dev
```

## 6. Open in browser

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

---

## Cloud deployment (aanbevolen)

### Railway (backend)

1. Push naar GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
gh repo create stockpulse-ai --public --push
```

2. Ga naar https://railway.app
3. "New Project" → "Deploy from GitHub"
4. Selecteer repo, set root: `backend`
5. Variables:
   - `DATABASE_URL=sqlite:///./stockpulse.db`
   - `SECRET_KEY=randomstring32chars`
6. Custom start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Vercel (frontend)

1. Ga naar https://vercel.com
2. Import GitHub repo
3. Root: `frontend`
4. Env var: `NEXT_PUBLIC_API_URL=https://jouw-railway-url.up.railway.app`

---

## Test de API

```bash
# Health check
curl http://localhost:8000/api/health

# Genereer eerste digest (duurt ~2 min)
curl -X POST http://localhost:8000/api/digest/generate

# Bekijk laatste digest
curl http://localhost:8000/api/digest/latest

# Check verificatie status
curl http://localhost:8000/api/verification/status
```
