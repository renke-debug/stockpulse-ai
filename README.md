# StockPulse - Drawdown Strategy

A simple QQQ drawdown-based accumulation strategy with guiderails.

## Strategy

Based on the [NexusTrade article](https://nexustrade.io/blog/i-asked-claude-opus-45-to-autonomously-develop-a-trading-strategy-it-is-destroying-the-market-20251125) about Claude Opus 4.5's autonomous trading strategy.

### Rules

| Condition | Action |
|-----------|--------|
| Drawdown < 20%, 7+ days since last buy | Buy €500 |
| Drawdown > 20%, 5+ days since last buy | Buy €1,500 |
| Position up > 40% | Sell 25% |

### Guiderails

- **Max position:** €10,000
- **Stop-loss alert:** -25%
- **Min cash reserve:** €2,000

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Usage

1. Open http://localhost:3000
2. Check the current signal
3. Execute trades manually via your broker
4. Click "I executed this" to record the trade

## API Endpoints

- `GET /api/signal` - Current trading signal
- `GET /api/status` - Full portfolio status
- `POST /api/execute/buy` - Record a buy
- `POST /api/execute/sell` - Record a sell
- `GET /api/history` - Price/drawdown history

## Deployment

The app is designed to run locally. For cloud deployment:
- Backend: Render/Railway
- Frontend: Vercel

Set `NEXT_PUBLIC_API_URL` in Vercel to your backend URL.

## Disclaimer

⚠️ Not financial advice. Use at your own risk.
