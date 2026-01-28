"""
Technical indicators calculator using yfinance historical data.
Calculates RSI, SMA crossovers, and 52-week range positioning.
"""

from typing import Optional
import pandas as pd
from app.services.market_data import get_historical_data


class TechnicalSignals:
    """Container for technical analysis signals."""

    def __init__(
        self,
        ticker: str,
        rsi: Optional[float] = None,
        rsi_signal: Optional[str] = None,
        sma_20: Optional[float] = None,
        sma_50: Optional[float] = None,
        sma_signal: Optional[str] = None,
        price_vs_52w: Optional[float] = None,
        range_signal: Optional[str] = None,
        overall_signal: Optional[str] = None,
        score: Optional[float] = None,
        error: Optional[str] = None,
    ):
        self.ticker = ticker
        self.rsi = rsi
        self.rsi_signal = rsi_signal
        self.sma_20 = sma_20
        self.sma_50 = sma_50
        self.sma_signal = sma_signal
        self.price_vs_52w = price_vs_52w
        self.range_signal = range_signal
        self.overall_signal = overall_signal
        self.score = score
        self.error = error

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "rsi": round(self.rsi, 2) if self.rsi else None,
            "rsi_signal": self.rsi_signal,
            "sma_20": round(self.sma_20, 2) if self.sma_20 else None,
            "sma_50": round(self.sma_50, 2) if self.sma_50 else None,
            "sma_signal": self.sma_signal,
            "price_vs_52w": round(self.price_vs_52w, 2) if self.price_vs_52w else None,
            "range_signal": self.range_signal,
            "overall_signal": self.overall_signal,
            "score": round(self.score, 2) if self.score else None,
            "error": self.error,
        }


def calculate_rsi(prices: pd.Series, period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index.

    Args:
        prices: Series of closing prices
        period: RSI period (default 14)

    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if len(prices) < period + 1:
        return None

    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None


def calculate_sma(prices: pd.Series, period: int) -> Optional[float]:
    """
    Calculate Simple Moving Average.

    Args:
        prices: Series of closing prices
        period: SMA period

    Returns:
        SMA value or None if insufficient data
    """
    if len(prices) < period:
        return None

    sma = prices.rolling(window=period).mean()
    return float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None


def get_rsi_signal(rsi: float) -> tuple[str, float]:
    """
    Interpret RSI value into signal and score.

    Returns:
        Tuple of (signal string, score from -1 to 1)
    """
    if rsi >= 70:
        return "Overbought", -0.5  # Bearish
    elif rsi >= 60:
        return "Bullish", 0.3
    elif rsi <= 30:
        return "Oversold", 0.5  # Bullish (potential reversal)
    elif rsi <= 40:
        return "Bearish", -0.3
    else:
        return "Neutral", 0.0


def get_sma_signal(sma_20: float, sma_50: float, current_price: float) -> tuple[str, float]:
    """
    Interpret SMA crossover into signal and score.

    Returns:
        Tuple of (signal string, score from -1 to 1)
    """
    # Golden cross: 20 SMA above 50 SMA
    if sma_20 > sma_50:
        if current_price > sma_20:
            return "Strong Bullish", 0.8
        else:
            return "Bullish", 0.4
    # Death cross: 20 SMA below 50 SMA
    else:
        if current_price < sma_20:
            return "Strong Bearish", -0.8
        else:
            return "Bearish", -0.4


def get_range_signal(price_pct: float) -> tuple[str, float]:
    """
    Interpret 52-week range position into signal and score.

    Args:
        price_pct: Position in range (0 = at low, 100 = at high)

    Returns:
        Tuple of (signal string, score from -1 to 1)
    """
    if price_pct >= 90:
        return "Near 52w High", -0.3  # Slightly bearish (extended)
    elif price_pct >= 70:
        return "Upper Range", 0.2
    elif price_pct <= 10:
        return "Near 52w Low", 0.3  # Potentially oversold
    elif price_pct <= 30:
        return "Lower Range", -0.2
    else:
        return "Mid Range", 0.0


def calc_technicals(ticker: str) -> TechnicalSignals:
    """
    Calculate all technical indicators for a stock.

    Args:
        ticker: Stock ticker symbol

    Returns:
        TechnicalSignals object with all indicators and signals
    """
    # Get 3 months of historical data
    hist = get_historical_data(ticker, period="3mo")

    if hist is None or hist.empty:
        return TechnicalSignals(ticker=ticker, error="No historical data available")

    close = hist["Close"]
    current_price = float(close.iloc[-1])

    # Calculate indicators
    rsi = calculate_rsi(close)
    sma_20 = calculate_sma(close, 20)
    sma_50 = calculate_sma(close, 50)

    # 52-week high/low from longer history
    hist_1y = get_historical_data(ticker, period="1y")
    if hist_1y is not None and not hist_1y.empty:
        high_52w = float(hist_1y["High"].max())
        low_52w = float(hist_1y["Low"].min())
        price_vs_52w = ((current_price - low_52w) / (high_52w - low_52w)) * 100
    else:
        price_vs_52w = None

    # Get signals and scores
    rsi_signal, rsi_score = ("N/A", 0) if rsi is None else get_rsi_signal(rsi)
    sma_signal, sma_score = ("N/A", 0) if (sma_20 is None or sma_50 is None) else get_sma_signal(sma_20, sma_50, current_price)
    range_signal, range_score = ("N/A", 0) if price_vs_52w is None else get_range_signal(price_vs_52w)

    # Calculate overall technical score (weighted average)
    weights = {"rsi": 0.3, "sma": 0.5, "range": 0.2}
    overall_score = (
        rsi_score * weights["rsi"] +
        sma_score * weights["sma"] +
        range_score * weights["range"]
    )

    # Determine overall signal
    if overall_score >= 0.4:
        overall_signal = "Bullish"
    elif overall_score >= 0.1:
        overall_signal = "Slightly Bullish"
    elif overall_score <= -0.4:
        overall_signal = "Bearish"
    elif overall_score <= -0.1:
        overall_signal = "Slightly Bearish"
    else:
        overall_signal = "Neutral"

    return TechnicalSignals(
        ticker=ticker,
        rsi=rsi,
        rsi_signal=rsi_signal,
        sma_20=sma_20,
        sma_50=sma_50,
        sma_signal=sma_signal,
        price_vs_52w=price_vs_52w,
        range_signal=range_signal,
        overall_signal=overall_signal,
        score=overall_score,
    )
