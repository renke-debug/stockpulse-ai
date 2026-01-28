"""
Multi-factor scoring engine.
Combines technicals, sentiment, and fundamentals into a single buy/sell score.
"""

from typing import Optional
from dataclasses import dataclass
from app.services.market_data import fetch_stock_data, StockData
from app.services.technicals import calc_technicals, TechnicalSignals
from app.services.news_scraper import fetch_news_for_ticker
from app.services.sentiment import aggregate_sentiment


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of score components."""
    technical_score: float
    technical_weight: float
    sentiment_score: float
    sentiment_weight: float
    fundamental_score: float
    fundamental_weight: float

    def to_dict(self) -> dict:
        return {
            "technical": {
                "score": round(self.technical_score, 2),
                "weight": self.technical_weight,
                "contribution": round(self.technical_score * self.technical_weight, 2),
            },
            "sentiment": {
                "score": round(self.sentiment_score, 2),
                "weight": self.sentiment_weight,
                "contribution": round(self.sentiment_score * self.sentiment_weight, 2),
            },
            "fundamental": {
                "score": round(self.fundamental_score, 2),
                "weight": self.fundamental_weight,
                "contribution": round(self.fundamental_score * self.fundamental_weight, 2),
            },
        }


@dataclass
class StockScore:
    """Complete scoring result for a stock."""
    ticker: str
    name: str
    score: float  # -100 to +100
    signal: str  # "Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"
    breakdown: ScoreBreakdown
    current_price: Optional[float]
    day_change_pct: Optional[float]
    pe_ratio: Optional[float]
    news_headlines: list[str]
    explanation: str
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "score": round(self.score, 1),
            "signal": self.signal,
            "breakdown": self.breakdown.to_dict(),
            "current_price": self.current_price,
            "day_change_pct": self.day_change_pct,
            "pe_ratio": self.pe_ratio,
            "news_headlines": self.news_headlines,
            "explanation": self.explanation,
            "error": self.error,
        }


# Weights for each factor
WEIGHTS = {
    "technical": 0.40,
    "sentiment": 0.30,
    "fundamental": 0.30,
}

# Sector average P/E ratios (simplified)
SECTOR_PE = {
    "Technology": 28,
    "Health Care": 22,
    "Financials": 14,
    "Consumer Discretionary": 25,
    "Consumer Staples": 22,
    "Industrials": 20,
    "Energy": 12,
    "Utilities": 18,
    "Communication Services": 20,
    "Real Estate": 35,
    "Materials": 15,
}


def calculate_fundamental_score(stock_data: StockData, sector: Optional[str]) -> float:
    """
    Calculate fundamental score based on P/E ratio vs sector average.

    Returns:
        Score from -1 to 1
    """
    if stock_data.pe_ratio is None:
        return 0.0

    pe = stock_data.pe_ratio
    sector_avg = SECTOR_PE.get(sector, 20)

    # Calculate how much better/worse than sector average
    # Lower P/E = better value = positive score
    pe_ratio_diff = (sector_avg - pe) / sector_avg

    # Clamp and scale to -1 to 1
    return max(-1.0, min(1.0, pe_ratio_diff))


def get_signal_from_score(score: float) -> str:
    """Convert score to signal label."""
    if score >= 60:
        return "Strong Buy"
    elif score >= 30:
        return "Buy"
    elif score >= -30:
        return "Hold"
    elif score >= -60:
        return "Sell"
    else:
        return "Strong Sell"


def generate_explanation(
    ticker: str,
    name: str,
    score: float,
    technicals: TechnicalSignals,
    sentiment_score: float,
    fundamental_score: float,
    news_headlines: list[str],
) -> str:
    """Generate human-readable explanation for the score."""
    parts = []

    # Overall direction
    if score >= 30:
        parts.append(f"{name} ({ticker}) krijgt een positief signaal.")
    elif score <= -30:
        parts.append(f"{name} ({ticker}) krijgt een negatief signaal.")
    else:
        parts.append(f"{name} ({ticker}) is momenteel neutraal.")

    # Technical factor
    if technicals.overall_signal and technicals.overall_signal != "Neutral":
        if "Bullish" in technicals.overall_signal:
            parts.append(f"Technisch beeld is {technicals.overall_signal.lower()} met RSI op {technicals.rsi:.0f}." if technicals.rsi else "")
        else:
            parts.append(f"Technisch beeld is {technicals.overall_signal.lower()}.")

    # Sentiment factor
    if sentiment_score > 0.2:
        parts.append("Nieuwssentiment is positief.")
    elif sentiment_score < -0.2:
        parts.append("Nieuwssentiment is negatief.")

    # Fundamental factor
    if fundamental_score > 0.2:
        parts.append("Waardering is aantrekkelijk vs sector.")
    elif fundamental_score < -0.2:
        parts.append("Waardering is duur vs sector.")

    return " ".join([p for p in parts if p])


def calculate_score(ticker: str, name: str, sector: Optional[str] = None) -> StockScore:
    """
    Calculate complete multi-factor score for a stock.

    Args:
        ticker: Stock ticker symbol
        name: Company name
        sector: Company sector for P/E comparison

    Returns:
        StockScore object with all details
    """
    # 1. Get market data
    stock_data = fetch_stock_data(ticker)
    if stock_data.error:
        return StockScore(
            ticker=ticker,
            name=name,
            score=0,
            signal="Hold",
            breakdown=ScoreBreakdown(0, 0.4, 0, 0.3, 0, 0.3),
            current_price=None,
            day_change_pct=None,
            pe_ratio=None,
            news_headlines=[],
            explanation=f"Geen data beschikbaar voor {ticker}",
            error=stock_data.error,
        )

    # 2. Calculate technical score
    technicals = calc_technicals(ticker)
    technical_score = technicals.score if technicals.score else 0.0

    # 3. Calculate sentiment score
    news = fetch_news_for_ticker(ticker, max_items=10)
    headlines = [n.title for n in news]
    sentiment_score = aggregate_sentiment(headlines) if headlines else 0.0

    # 4. Calculate fundamental score
    fundamental_score = calculate_fundamental_score(stock_data, sector)

    # 5. Combine scores with weights
    combined_score = (
        technical_score * WEIGHTS["technical"] +
        sentiment_score * WEIGHTS["sentiment"] +
        fundamental_score * WEIGHTS["fundamental"]
    )

    # Scale to -100 to +100
    final_score = combined_score * 100

    # Generate signal and explanation
    signal = get_signal_from_score(final_score)
    explanation = generate_explanation(
        ticker, name, final_score,
        technicals, sentiment_score, fundamental_score, headlines
    )

    return StockScore(
        ticker=ticker,
        name=name,
        score=final_score,
        signal=signal,
        breakdown=ScoreBreakdown(
            technical_score=technical_score,
            technical_weight=WEIGHTS["technical"],
            sentiment_score=sentiment_score,
            sentiment_weight=WEIGHTS["sentiment"],
            fundamental_score=fundamental_score,
            fundamental_weight=WEIGHTS["fundamental"],
        ),
        current_price=stock_data.price,
        day_change_pct=stock_data.day_change_pct,
        pe_ratio=stock_data.pe_ratio,
        news_headlines=headlines[:3],  # Top 3 headlines
        explanation=explanation,
    )
