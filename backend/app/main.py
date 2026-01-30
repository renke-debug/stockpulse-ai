from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import os

from app.strategy import DrawdownStrategy

app = FastAPI(title="StockPulse - Drawdown Strategy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize strategy
strategy = DrawdownStrategy(
    ticker="QQQ",
    normal_buy_amount=500,
    aggressive_buy_amount=1500,
    drawdown_threshold=20,  # percentage
    profit_take_threshold=40,  # percentage
    max_position=10000,
    min_days_normal=7,
    min_days_aggressive=5,
)

# Simple file-based storage for state
STATE_FILE = "data/state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {
        "positions": [],  # list of {date, price, amount}
        "last_buy_date": None,
        "total_invested": 0,
        "cash_reserve": 2000,
    }

def save_state(state):
    os.makedirs("data", exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


@app.get("/")
def root():
    return {"app": "StockPulse - Drawdown Strategy", "status": "running"}


@app.get("/api/signal")
def get_signal():
    """Get current trading signal based on strategy rules."""
    state = load_state()
    signal = strategy.get_signal(state)
    return signal


@app.get("/api/status")
def get_status():
    """Get current portfolio status and metrics."""
    state = load_state()
    status = strategy.get_status(state)
    return status


@app.post("/api/execute/{action}")
def execute_action(action: str, amount: float = None):
    """
    Record a manual trade execution.
    action: 'buy' or 'sell'
    amount: euro amount (optional, uses signal amount if not provided)
    """
    state = load_state()

    if action == "buy":
        signal = strategy.get_signal(state)
        if signal["action"] != "BUY":
            return {"error": "No buy signal active", "signal": signal}

        buy_amount = amount or signal["amount"]
        current_price = strategy.get_current_price()

        if state["total_invested"] + buy_amount > strategy.max_position:
            return {"error": f"Would exceed max position of €{strategy.max_position}"}

        state["positions"].append({
            "date": datetime.now().isoformat(),
            "price": current_price,
            "amount": buy_amount,
            "shares": buy_amount / current_price
        })
        state["last_buy_date"] = datetime.now().date().isoformat()
        state["total_invested"] += buy_amount

        save_state(state)
        return {
            "status": "recorded",
            "action": "BUY",
            "amount": buy_amount,
            "price": current_price,
            "total_invested": state["total_invested"]
        }

    elif action == "sell":
        signal = strategy.get_signal(state)

        if not state["positions"]:
            return {"error": "No positions to sell"}

        current_price = strategy.get_current_price()
        sell_percentage = 0.25  # Sell 25% on profit take

        total_shares = sum(p["shares"] for p in state["positions"])
        shares_to_sell = total_shares * sell_percentage
        sell_value = shares_to_sell * current_price

        # Reduce positions proportionally
        for p in state["positions"]:
            p["shares"] *= (1 - sell_percentage)

        state["total_invested"] *= (1 - sell_percentage)

        # Remove empty positions
        state["positions"] = [p for p in state["positions"] if p["shares"] > 0.001]

        save_state(state)
        return {
            "status": "recorded",
            "action": "SELL",
            "shares_sold": shares_to_sell,
            "value": sell_value,
            "price": current_price,
            "remaining_invested": state["total_invested"]
        }

    return {"error": "Invalid action. Use 'buy' or 'sell'"}


@app.post("/api/reset")
def reset_state():
    """Reset all state (for testing)."""
    state = {
        "positions": [],
        "last_buy_date": None,
        "total_invested": 0,
        "cash_reserve": 2000,
    }
    save_state(state)
    return {"status": "reset", "state": state}


@app.get("/api/history")
def get_history():
    """Get price history and drawdown chart data."""
    return strategy.get_history()
