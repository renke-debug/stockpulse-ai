"""
Daily digest generator.
Scores all tracked stocks and selects top 5 buy/sell recommendations.
Now also logs predictions for verification tracking.
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.models.stock import Stock
from app.models.digest import Digest
from app.services.scoring import calculate_score, StockScore
from app.services.verification import log_prediction


def load_tracked_stocks() -> list[dict]:
    """Load tracked stocks from JSON file."""
    json_path = Path(__file__).parent.parent.parent / "data" / "stocks_sp100.json"
    with open(json_path, "r") as f:
        return json.load(f)


def score_all_stocks(stocks: list[dict], progress_callback=None) -> list[StockScore]:
    """
    Calculate scores for all stocks.

    Args:
        stocks: List of stock dicts with ticker, name, sector
        progress_callback: Optional callback(current, total) for progress updates

    Returns:
        List of StockScore objects
    """
    scores = []
    total = len(stocks)

    for i, stock in enumerate(stocks):
        if progress_callback:
            progress_callback(i + 1, total)

        try:
            score = calculate_score(
                ticker=stock["ticker"],
                name=stock["name"],
                sector=stock.get("sector"),
            )
            scores.append(score)
        except Exception as e:
            print(f"Error scoring {stock['ticker']}: {e}")
            continue

    return scores


def select_top_picks(scores: list[StockScore], top_n: int = 5) -> tuple[list[StockScore], list[StockScore]]:
    """
    Select top buy and sell picks.

    Args:
        scores: List of all stock scores
        top_n: Number of picks per category

    Returns:
        Tuple of (buy_picks, sell_picks)
    """
    # Filter out errors
    valid_scores = [s for s in scores if s.error is None]

    # Sort by score descending
    sorted_scores = sorted(valid_scores, key=lambda x: x.score, reverse=True)

    # Top N positive scores = buy picks
    buy_picks = [s for s in sorted_scores[:top_n] if s.score > 0]

    # Bottom N negative scores = sell picks
    sell_picks = [s for s in sorted_scores[-top_n:] if s.score < 0]
    sell_picks.reverse()  # Most negative first

    return buy_picks, sell_picks


def format_pick_for_digest(pick: StockScore, user_budget: float = 10000.0) -> dict:
    """
    Format a pick for the digest with suggested position size.

    Args:
        pick: StockScore object
        user_budget: User's total budget for position sizing

    Returns:
        Dict formatted for digest display
    """
    # Max 10% of budget per position
    max_position = user_budget * 0.10
    suggested_position = max_position

    # Scale down for lower confidence scores
    confidence = abs(pick.score) / 100
    suggested_position *= confidence

    return {
        "ticker": pick.ticker,
        "name": pick.name,
        "score": round(pick.score, 1),
        "signal": pick.signal,
        "current_price": pick.current_price,
        "day_change_pct": pick.day_change_pct,
        "explanation": pick.explanation,
        "suggested_position": round(suggested_position, 2),
        "news_headlines": pick.news_headlines,
        "breakdown": pick.breakdown.to_dict(),
    }


def generate_digest(db: Optional[Session] = None, save_to_db: bool = True) -> dict:
    """
    Generate the daily digest.

    Args:
        db: Database session (optional, created if not provided)
        save_to_db: Whether to save digest to database

    Returns:
        Digest data dict
    """
    print(f"Starting digest generation at {datetime.now()}")

    # Load stocks
    stocks = load_tracked_stocks()
    print(f"Loaded {len(stocks)} stocks to analyze")

    # Score all stocks
    def progress(current, total):
        if current % 10 == 0 or current == total:
            print(f"Progress: {current}/{total} stocks scored")

    scores = score_all_stocks(stocks, progress_callback=progress)
    print(f"Scored {len(scores)} stocks successfully")

    # Select top picks
    buy_picks, sell_picks = select_top_picks(scores, top_n=5)
    print(f"Selected {len(buy_picks)} buy picks and {len(sell_picks)} sell picks")

    # Format digest
    digest_data = {
        "buy": [format_pick_for_digest(p) for p in buy_picks],
        "sell": [format_pick_for_digest(p) for p in sell_picks],
    }

    # Save to database
    if save_to_db:
        if db is None:
            db = SessionLocal()
            close_db = True
        else:
            close_db = False

        try:
            today = date.today().isoformat()

            # Check if digest already exists for today
            existing = db.query(Digest).filter(Digest.date == today).first()
            if existing:
                existing.data = digest_data
                existing.generated_at = datetime.now()
            else:
                digest = Digest(
                    date=today,
                    data=digest_data,
                )
                db.add(digest)

            # === LOG PREDICTIONS FOR VERIFICATION ===
            print("Logging predictions for verification tracking...")

            for pick in buy_picks:
                if pick.current_price:
                    log_prediction(
                        db=db,
                        ticker=pick.ticker,
                        company_name=pick.name,
                        direction="buy",
                        score=pick.score,
                        price=pick.current_price,
                    )
                    print(f"  Logged BUY prediction: {pick.ticker} @ ${pick.current_price}")

            for pick in sell_picks:
                if pick.current_price:
                    log_prediction(
                        db=db,
                        ticker=pick.ticker,
                        company_name=pick.name,
                        direction="sell",
                        score=pick.score,
                        price=pick.current_price,
                    )
                    print(f"  Logged SELL prediction: {pick.ticker} @ ${pick.current_price}")

            db.commit()
            print(f"Digest and predictions saved to database for {today}")

        finally:
            if close_db:
                db.close()

    return {
        "date": date.today().isoformat(),
        "generated_at": datetime.now().isoformat(),
        **digest_data,
    }


def get_latest_digest(db: Session) -> Optional[dict]:
    """
    Get the most recent digest from database.

    Args:
        db: Database session

    Returns:
        Digest data dict or None
    """
    digest = db.query(Digest).order_by(Digest.date.desc()).first()

    if digest is None:
        return None

    return {
        "date": digest.date,
        "generated_at": digest.generated_at.isoformat() if digest.generated_at else None,
        **digest.data,
    }


def get_digest_by_date(db: Session, digest_date: str) -> Optional[dict]:
    """
    Get digest for a specific date.

    Args:
        db: Database session
        digest_date: Date string (YYYY-MM-DD)

    Returns:
        Digest data dict or None
    """
    digest = db.query(Digest).filter(Digest.date == digest_date).first()

    if digest is None:
        return None

    return {
        "date": digest.date,
        "generated_at": digest.generated_at.isoformat() if digest.generated_at else None,
        **digest.data,
    }


# CLI entry point
if __name__ == "__main__":
    from app.models.database import init_db

    print("Initializing database...")
    init_db()

    print("Generating digest...")
    result = generate_digest()

    print("\n=== DAILY DIGEST ===")
    print(f"Date: {result['date']}")
    print(f"Generated: {result['generated_at']}")

    print("\n📈 TOP 5 BUY SIGNALS:")
    for i, pick in enumerate(result["buy"], 1):
        print(f"  {i}. {pick['ticker']} ({pick['name']})")
        print(f"     Score: {pick['score']} | {pick['signal']}")
        print(f"     {pick['explanation']}")

    print("\n📉 TOP 5 SELL SIGNALS:")
    for i, pick in enumerate(result["sell"], 1):
        print(f"  {i}. {pick['ticker']} ({pick['name']})")
        print(f"     Score: {pick['score']} | {pick['signal']}")
        print(f"     {pick['explanation']}")
