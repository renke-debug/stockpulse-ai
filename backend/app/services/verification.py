"""
Verification service.
Tracks predictions and verifies them after 1, 7, and 30 days.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.prediction import Prediction, VerificationStats
from app.services.market_data import fetch_stock_data


def log_prediction(
    db: Session,
    ticker: str,
    company_name: str,
    direction: str,  # "buy" or "sell"
    score: float,
    price: float,
) -> Prediction:
    """
    Log a new prediction when advice is generated.
    Called automatically when digest is created.
    """
    prediction = Prediction(
        ticker=ticker,
        company_name=company_name,
        direction=direction,
        score=score,
        price_at_prediction=price,
        prediction_date=datetime.utcnow(),
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def verify_prediction(prediction: Prediction, current_price: float, days: int) -> dict:
    """
    Verify a single prediction against current price.

    Returns dict with:
    - correct: bool - was direction prediction correct?
    - return_pct: float - percentage return if you followed advice
    """
    price_change = current_price - prediction.price_at_prediction
    return_pct = (price_change / prediction.price_at_prediction) * 100

    # For BUY: correct if price went up
    # For SELL: correct if price went down (you'd profit by not holding/shorting)
    if prediction.direction == "buy":
        correct = price_change > 0
        actual_return = return_pct
    else:  # sell
        correct = price_change < 0
        actual_return = -return_pct  # Inverse: if price dropped, that's positive for sell advice

    return {
        "correct": correct,
        "return_pct": round(actual_return, 2),
        "current_price": current_price,
    }


def run_verification(db: Session) -> dict:
    """
    Run verification on all predictions that need checking.
    Called daily by cron job.

    Returns summary of what was verified.
    """
    now = datetime.utcnow()
    results = {
        "verified_1d": 0,
        "verified_7d": 0,
        "verified_30d": 0,
        "errors": [],
    }

    # Get predictions needing 1-day verification (older than 1 day, not yet verified)
    one_day_ago = now - timedelta(days=1)
    predictions_1d = db.query(Prediction).filter(
        and_(
            Prediction.prediction_date <= one_day_ago,
            Prediction.verified_1d == False,
        )
    ).all()

    for pred in predictions_1d:
        try:
            stock_data = fetch_stock_data(pred.ticker)
            if stock_data.price:
                result = verify_prediction(pred, stock_data.price, 1)
                pred.price_after_1d = result["current_price"]
                pred.correct_1d = result["correct"]
                pred.return_1d = result["return_pct"]
                pred.verified_1d = True
                results["verified_1d"] += 1
        except Exception as e:
            results["errors"].append(f"1d {pred.ticker}: {str(e)}")

    # Get predictions needing 7-day verification
    seven_days_ago = now - timedelta(days=7)
    predictions_7d = db.query(Prediction).filter(
        and_(
            Prediction.prediction_date <= seven_days_ago,
            Prediction.verified_7d == False,
        )
    ).all()

    for pred in predictions_7d:
        try:
            stock_data = fetch_stock_data(pred.ticker)
            if stock_data.price:
                result = verify_prediction(pred, stock_data.price, 7)
                pred.price_after_7d = result["current_price"]
                pred.correct_7d = result["correct"]
                pred.return_7d = result["return_pct"]
                pred.verified_7d = True
                results["verified_7d"] += 1
        except Exception as e:
            results["errors"].append(f"7d {pred.ticker}: {str(e)}")

    # Get predictions needing 30-day verification
    thirty_days_ago = now - timedelta(days=30)
    predictions_30d = db.query(Prediction).filter(
        and_(
            Prediction.prediction_date <= thirty_days_ago,
            Prediction.verified_30d == False,
        )
    ).all()

    for pred in predictions_30d:
        try:
            stock_data = fetch_stock_data(pred.ticker)
            if stock_data.price:
                result = verify_prediction(pred, stock_data.price, 30)
                pred.price_after_30d = result["current_price"]
                pred.correct_30d = result["correct"]
                pred.return_30d = result["return_pct"]
                pred.verified_30d = True
                results["verified_30d"] += 1
        except Exception as e:
            results["errors"].append(f"30d {pred.ticker}: {str(e)}")

    db.commit()

    # Update aggregated stats
    update_verification_stats(db)

    return results


def update_verification_stats(db: Session) -> VerificationStats:
    """
    Calculate and store aggregated verification statistics.
    """
    # Count totals
    total = db.query(Prediction).count()

    # 1-day stats
    verified_1d = db.query(Prediction).filter(Prediction.verified_1d == True).all()
    correct_1d = [p for p in verified_1d if p.correct_1d]
    accuracy_1d = (len(correct_1d) / len(verified_1d) * 100) if verified_1d else None
    avg_return_1d = sum(p.return_1d for p in verified_1d if p.return_1d) / len(verified_1d) if verified_1d else None

    # 7-day stats
    verified_7d = db.query(Prediction).filter(Prediction.verified_7d == True).all()
    correct_7d = [p for p in verified_7d if p.correct_7d]
    accuracy_7d = (len(correct_7d) / len(verified_7d) * 100) if verified_7d else None
    avg_return_7d = sum(p.return_7d for p in verified_7d if p.return_7d) / len(verified_7d) if verified_7d else None

    # 30-day stats
    verified_30d = db.query(Prediction).filter(Prediction.verified_30d == True).all()
    correct_30d = [p for p in verified_30d if p.correct_30d]
    accuracy_30d = (len(correct_30d) / len(verified_30d) * 100) if verified_30d else None
    avg_return_30d = sum(p.return_30d for p in verified_30d if p.return_30d) / len(verified_30d) if verified_30d else None

    # Hypothetical total return (sum of all 7d returns as main metric)
    hypothetical_return = sum(p.return_7d for p in verified_7d if p.return_7d) if verified_7d else None

    # Check unlock criteria: >55% accuracy on 7d horizon with 50+ verified predictions
    is_unlocked = False
    unlock_reason = None

    if len(verified_7d) >= 50:
        if accuracy_7d and accuracy_7d >= 55:
            is_unlocked = True
            unlock_reason = f"Achieved {accuracy_7d:.1f}% accuracy over {len(verified_7d)} predictions"
        else:
            unlock_reason = f"Accuracy {accuracy_7d:.1f}% < 55% required ({len(verified_7d)} predictions)"
    else:
        unlock_reason = f"Need {50 - len(verified_7d)} more verified predictions (have {len(verified_7d)}/50)"

    # Create new stats record
    stats = VerificationStats(
        total_predictions=total,
        verified_1d_count=len(verified_1d),
        correct_1d_count=len(correct_1d),
        accuracy_1d=round(accuracy_1d, 1) if accuracy_1d else None,
        avg_return_1d=round(avg_return_1d, 2) if avg_return_1d else None,
        verified_7d_count=len(verified_7d),
        correct_7d_count=len(correct_7d),
        accuracy_7d=round(accuracy_7d, 1) if accuracy_7d else None,
        avg_return_7d=round(avg_return_7d, 2) if avg_return_7d else None,
        verified_30d_count=len(verified_30d),
        correct_30d_count=len(correct_30d),
        accuracy_30d=round(accuracy_30d, 1) if accuracy_30d else None,
        avg_return_30d=round(avg_return_30d, 2) if avg_return_30d else None,
        hypothetical_return_total=round(hypothetical_return, 2) if hypothetical_return else None,
        is_unlocked=is_unlocked,
        unlock_reason=unlock_reason,
    )

    db.add(stats)
    db.commit()
    db.refresh(stats)

    return stats


def get_latest_stats(db: Session) -> Optional[VerificationStats]:
    """Get most recent verification stats."""
    return db.query(VerificationStats).order_by(VerificationStats.calculated_at.desc()).first()


def get_prediction_history(db: Session, limit: int = 100) -> list[Prediction]:
    """Get recent predictions with their verification status."""
    return db.query(Prediction).order_by(Prediction.prediction_date.desc()).limit(limit).all()


def is_system_unlocked(db: Session) -> tuple[bool, str]:
    """
    Check if system is unlocked for real trading advice.
    Returns (is_unlocked, reason_message)
    """
    stats = get_latest_stats(db)
    if not stats:
        return False, "Nog geen verificatie data. Wacht tot eerste voorspellingen zijn geverifieerd."

    return stats.is_unlocked, stats.unlock_reason
