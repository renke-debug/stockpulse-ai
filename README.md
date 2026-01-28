# StockPulse AI

AI-gestuurde dagelijkse stock advisory voor beginnende beleggers.

## Features

- 📈 Daily top 5 buy signals
- 📉 Daily top 5 sell signals
- 🤖 Multi-factor AI scoring (technisch, sentiment, fundamenteel)
- 💰 Budget-based position sizing
- 📱 Responsive webapp

## Tech Stack

**Backend**
- Python 3.11 + FastAPI
- SQLite + SQLAlchemy
- yfinance (gratis market data)
- RSS feeds voor nieuws

**Frontend**
- Next.js 14 + TypeScript
- TailwindCSS
- JWT authentication

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database with stocks
python -c "from app.models.database import init_db; init_db()"
python -m app.services.seed_stocks

# Run API server
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

## Generate Digest

```bash
cd backend
python generate_daily.py
```

Of via API:
```bash
curl -X POST http://localhost:8000/api/digest/generate
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/user/register` | POST | Create account |
| `/api/user/login` | POST | Login |
| `/api/user/me` | GET | Get profile |
| `/api/user/budget` | PATCH | Update budget |
| `/api/digest/latest` | GET | Latest digest |
| `/api/digest/{date}` | GET | Digest by date |
| `/api/digest/generate` | POST | Trigger generation |

## Deployment

### Railway (Backend)

1. Connect GitHub repo
2. Set root directory: `backend`
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Vercel (Frontend)

1. Connect GitHub repo
2. Set root directory: `frontend`
3. Add env var: `NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app`

## Disclaimer

⚠️ Dit is een experimenteel systeem. Geen financieel advies. Doe altijd je eigen onderzoek voordat je belegt.

## License

MIT
