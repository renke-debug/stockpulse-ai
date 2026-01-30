import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class DrawdownStrategy:
    """
    Drawdown-Based Accumulation Strategy

    Rules:
    - Normal buy: €500 when drawdown < 20% (max 1x per 7 days)
    - Aggressive buy: €1500 when drawdown > 20% (max 1x per 5 days)
    - Profit take: Sell 25% when position is up > 40%

    Guiderails:
    - Max position: €10,000 total
    - Stop-loss: Alert at -25% portfolio loss
    - Min cash reserve: €2,000
    """

    def __init__(
        self,
        ticker: str = "QQQ",
        normal_buy_amount: float = 500,
        aggressive_buy_amount: float = 1500,
        drawdown_threshold: float = 20,
        profit_take_threshold: float = 40,
        max_position: float = 10000,
        min_days_normal: int = 7,
        min_days_aggressive: int = 5,
        lookback_days: int = 252,
    ):
        self.ticker = ticker
        self.normal_buy_amount = normal_buy_amount
        self.aggressive_buy_amount = aggressive_buy_amount
        self.drawdown_threshold = drawdown_threshold
        self.profit_take_threshold = profit_take_threshold
        self.max_position = max_position
        self.min_days_normal = min_days_normal
        self.min_days_aggressive = min_days_aggressive
        self.lookback_days = lookback_days

        self._price_cache = None
        self._cache_time = None

    def _get_price_data(self) -> pd.DataFrame:
        """Fetch price data with caching (5 min)."""
        now = datetime.now()

        if self._price_cache is not None and self._cache_time:
            if (now - self._cache_time).seconds < 300:
                return self._price_cache

        ticker = yf.Ticker(self.ticker)
        df = ticker.history(period="1y")

        self._price_cache = df
        self._cache_time = now

        return df

    def get_current_price(self) -> float:
        """Get current price."""
        df = self._get_price_data()
        return float(df["Close"].iloc[-1])

    def get_drawdown(self) -> Dict[str, float]:
        """Calculate current drawdown from 252-day high."""
        df = self._get_price_data()

        # Use last 252 trading days (1 year)
        df_period = df.tail(self.lookback_days)

        peak = df_period["Close"].max()
        current = df_period["Close"].iloc[-1]
        drawdown = ((peak - current) / peak) * 100

        return {
            "current_price": float(current),
            "peak_price": float(peak),
            "drawdown_pct": float(drawdown),
            "peak_date": str(df_period["Close"].idxmax().date()),
        }

    def _days_since_last_buy(self, state: Dict) -> Optional[int]:
        """Calculate days since last buy."""
        if not state.get("last_buy_date"):
            return None

        last_buy = datetime.fromisoformat(state["last_buy_date"]).date()
        today = datetime.now().date()
        return (today - last_buy).days

    def get_signal(self, state: Dict) -> Dict[str, Any]:
        """
        Determine current trading signal.

        Returns:
            action: HOLD, BUY, SELL, STOP_LOSS
            signal_type: normal_buy, aggressive_buy, profit_take, stop_loss
            amount: suggested amount in euros
            reason: explanation
        """
        drawdown_info = self.get_drawdown()
        current_price = drawdown_info["current_price"]
        drawdown_pct = drawdown_info["drawdown_pct"]

        days_since_buy = self._days_since_last_buy(state)
        total_invested = state.get("total_invested", 0)
        positions = state.get("positions", [])

        # Calculate current portfolio value and P&L
        total_shares = sum(p.get("shares", 0) for p in positions)
        current_value = total_shares * current_price
        pnl_pct = ((current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0

        result = {
            "action": "HOLD",
            "signal_type": None,
            "amount": 0,
            "reason": "",
            "drawdown_pct": round(drawdown_pct, 2),
            "current_price": round(current_price, 2),
            "days_since_buy": days_since_buy,
            "total_invested": round(total_invested, 2),
            "current_value": round(current_value, 2),
            "pnl_pct": round(pnl_pct, 2),
            "timestamp": datetime.now().isoformat(),
        }

        # Check STOP LOSS first (-25% portfolio)
        if pnl_pct <= -25:
            result["action"] = "STOP_LOSS"
            result["signal_type"] = "stop_loss"
            result["reason"] = f"Portfolio down {pnl_pct:.1f}% - STOP LOSS triggered. Consider selling all."
            return result

        # Check PROFIT TAKE (>40% gain)
        if pnl_pct >= self.profit_take_threshold:
            result["action"] = "SELL"
            result["signal_type"] = "profit_take"
            result["amount"] = current_value * 0.25
            result["reason"] = f"Portfolio up {pnl_pct:.1f}% - Take 25% profit (€{result['amount']:.0f})"
            return result

        # Check if max position reached
        if total_invested >= self.max_position:
            result["reason"] = f"Max position (€{self.max_position}) reached. Holding."
            return result

        # Check AGGRESSIVE BUY (drawdown > 20%)
        if drawdown_pct >= self.drawdown_threshold:
            can_buy = days_since_buy is None or days_since_buy >= self.min_days_aggressive
            remaining_capacity = self.max_position - total_invested
            buy_amount = min(self.aggressive_buy_amount, remaining_capacity)

            if can_buy and buy_amount > 0:
                result["action"] = "BUY"
                result["signal_type"] = "aggressive_buy"
                result["amount"] = buy_amount
                result["reason"] = f"Drawdown {drawdown_pct:.1f}% > {self.drawdown_threshold}% - AGGRESSIVE BUY €{buy_amount:.0f}"
                return result
            else:
                wait_days = self.min_days_aggressive - (days_since_buy or 0)
                result["reason"] = f"Aggressive zone but wait {wait_days} more days"
                return result

        # Check NORMAL BUY (drawdown < 20%)
        can_buy = days_since_buy is None or days_since_buy >= self.min_days_normal
        remaining_capacity = self.max_position - total_invested
        buy_amount = min(self.normal_buy_amount, remaining_capacity)

        if can_buy and buy_amount > 0:
            result["action"] = "BUY"
            result["signal_type"] = "normal_buy"
            result["amount"] = buy_amount
            result["reason"] = f"Normal conditions - BUY €{buy_amount:.0f}"
            return result
        else:
            wait_days = self.min_days_normal - (days_since_buy or 0)
            result["reason"] = f"Wait {wait_days} more days for next buy"
            return result

    def get_status(self, state: Dict) -> Dict[str, Any]:
        """Get full portfolio status."""
        drawdown_info = self.get_drawdown()
        signal = self.get_signal(state)

        positions = state.get("positions", [])
        total_shares = sum(p.get("shares", 0) for p in positions)
        current_value = total_shares * drawdown_info["current_price"]
        total_invested = state.get("total_invested", 0)

        return {
            "ticker": self.ticker,
            "current_price": drawdown_info["current_price"],
            "drawdown": drawdown_info,
            "signal": signal,
            "portfolio": {
                "total_invested": round(total_invested, 2),
                "current_value": round(current_value, 2),
                "total_shares": round(total_shares, 4),
                "pnl_euro": round(current_value - total_invested, 2),
                "pnl_pct": round(((current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0, 2),
                "positions_count": len(positions),
                "remaining_capacity": round(self.max_position - total_invested, 2),
            },
            "guiderails": {
                "max_position": self.max_position,
                "stop_loss_pct": -25,
                "profit_take_pct": self.profit_take_threshold,
                "drawdown_threshold": self.drawdown_threshold,
            },
            "last_buy_date": state.get("last_buy_date"),
        }

    def get_history(self) -> Dict[str, Any]:
        """Get historical data for charts."""
        df = self._get_price_data()

        # Calculate rolling max and drawdown
        df["Peak"] = df["Close"].cummax()
        df["Drawdown"] = ((df["Peak"] - df["Close"]) / df["Peak"]) * 100

        # Convert to list format for frontend
        history = []
        for date, row in df.iterrows():
            history.append({
                "date": str(date.date()),
                "price": round(float(row["Close"]), 2),
                "peak": round(float(row["Peak"]), 2),
                "drawdown": round(float(row["Drawdown"]), 2),
            })

        return {
            "ticker": self.ticker,
            "data": history[-90:],  # Last 90 days
            "current": history[-1] if history else None,
        }
