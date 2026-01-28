"""
Yahoo Finance data fetcher service.
Fetches stock prices, fundamentals and historical data using yfinance (free).
"""

import time
from typing import Optional
import yfinance as yf
import pandas as pd


class StockData:
    """Container for stock market data."""

    def __init__(
        self,
        ticker: str,
        price: Optional[float] = None,
        volume: Optional[int] = None,
        day_change: Optional[float] = None,
        day_change_pct: Optional[float] = None,
        pe_ratio: Optional[float] = None,
        market_cap: Optional[float] = None,
        fifty_two_week_high: Optional[float] = None,
        fifty_two_week_low: Optional[float] = None,
        error: Optional[str] = None,
    ):
        self.ticker = ticker
        self.price = price
        self.volume = volume
        self.day_change = day_change
        self.day_change_pct = day_change_pct
        self.pe_ratio = pe_ratio
        self.market_cap = market_cap
        self.fifty_two_week_high = fifty_two_week_high
        self.fifty_two_week_low = fifty_two_week_low
        self.error = error

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "price": self.price,
            "volume": self.volume,
            "day_change": self.day_change,
            "day_change_pct": self.day_change_pct,
            "pe_ratio": self.pe_ratio,
            "market_cap": self.market_cap,
            "fifty_two_week_high": self.fifty_two_week_high,
            "fifty_two_week_low": self.fifty_two_week_low,
            "error": self.error,
        }


def fetch_stock_data(ticker: str) -> StockData:
    """
    Fetch current stock data for a single ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')

    Returns:
        StockData object with price and fundamental data
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Check if we got valid data
        if not info or "regularMarketPrice" not in info:
            return StockData(ticker=ticker, error="No data available")

        price = info.get("regularMarketPrice") or info.get("currentPrice")
        prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose")

        day_change = None
        day_change_pct = None
        if price and prev_close:
            day_change = price - prev_close
            day_change_pct = (day_change / prev_close) * 100

        return StockData(
            ticker=ticker,
            price=price,
            volume=info.get("regularMarketVolume") or info.get("volume"),
            day_change=round(day_change, 2) if day_change else None,
            day_change_pct=round(day_change_pct, 2) if day_change_pct else None,
            pe_ratio=info.get("trailingPE") or info.get("forwardPE"),
            market_cap=info.get("marketCap"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
            fifty_two_week_low=info.get("fiftyTwoWeekLow"),
        )

    except Exception as e:
        return StockData(ticker=ticker, error=str(e))


def fetch_batch_stock_data(
    tickers: list[str],
    batch_size: int = 100,
    delay_between_batches: float = 1.0,
) -> list[StockData]:
    """
    Fetch stock data for multiple tickers with rate limiting.

    Args:
        tickers: List of ticker symbols
        batch_size: Maximum tickers per batch (default 100)
        delay_between_batches: Seconds to wait between batches (default 1.0)

    Returns:
        List of StockData objects
    """
    results: list[StockData] = []

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]

        for ticker in batch:
            data = fetch_stock_data(ticker)
            results.append(data)

        # Rate limiting between batches
        if i + batch_size < len(tickers):
            time.sleep(delay_between_batches)

    return results


def get_historical_data(
    ticker: str,
    period: str = "3mo",
) -> Optional[pd.DataFrame]:
    """
    Get historical price data for technical analysis.

    Args:
        ticker: Stock ticker symbol
        period: Time period (1mo, 3mo, 6mo, 1y, etc.)

    Returns:
        DataFrame with OHLCV data or None if error
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            return None

        return hist

    except Exception:
        return None
