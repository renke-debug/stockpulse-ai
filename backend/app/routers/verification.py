"""
Verification API endpoints.
Exposes prediction tracking and accuracy statistics.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.models.database import get_db
from app.services.verification import (
    get_latest_stats,
    get_prediction_history,
    is_system_unlocked,
    run_verification,
    update_verification_stats,
)

router = APIRouter()


class PredictionResponse(BaseModel):
    id: int
    ticker: str
    company_name: str
    direction: str
    score: float
    prediction_date: datetime
    price_at_prediction: float

    # 1-day verification
    verified_1d: bool
    correct_1d: Optional[bool]
    return_1d: Optional[float]

    # 7-day verification
    verified_7d: bool
    correct_7d: Optional[bool]
    return_7d: Optional[float]

    # 30-day verification
    verified_30d: bool
    correct_30d: Optional[bool]
    return_30d: Optional[float]

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_predictions: int

    # 1-day
    verified_1d_count: int
    correct_1d_count: int
    accuracy_1d: Optional[float]
    avg_return_1d: Optional[float]

    # 7-day
    verified_7d_count: int
    correct_7d_count: int
    accuracy_7d: Optional[float]
    avg_return_7d: Optional[float]

    # 30-day
    verified_30d_count: int
    correct_30d_count: int
    accuracy_30d: Optional[float]
    avg_return_30d: Optional[float]

    # Portfolio
    hypothetical_return_total: Optional[float]

    # Unlock status
    is_unlocked: bool
    unlock_reason: Optional[str]

    calculated_at: datetime

    class Config:
        from_attributes = True


class UnlockRequirements(BaseModel):
    min_predictions: int
    min_accuracy: float
    current_predictions: int
    current_accuracy: Optional[float]


class SimplifiedStats(BaseModel):
    total_predictions: int
    verified_1d: int
    verified_7d: int
    verified_30d: int
    accuracy_1d: Optional[float]
    accuracy_7d: Optional[float]
    accuracy_30d: Optional[float]
    avg_return_1d: Optional[float]
    avg_return_7d: Optional[float]
    avg_return_30d: Optional[float]
    is_unlocked: bool
    unlock_reason: Optional[str]
    last_updated: Optional[datetime]


class SystemStatusResponse(BaseModel):
    is_unlocked: bool
    mode: str  # "observation" or "active"
    message: str
    stats: Optional[SimplifiedStats]
    unlock_requirements: UnlockRequirements


@router.get("/stats", response_model=Optional[SimplifiedStats])
async def get_stats(db: Session = Depends(get_db)):
    """
    Get latest verification statistics.
    Shows accuracy percentages and unlock status.
    """
    stats = get_latest_stats(db)
    if not stats:
        return None

    return SimplifiedStats(
        total_predictions=stats.total_predictions,
        verified_1d=stats.verified_1d_count,
        verified_7d=stats.verified_7d_count,
        verified_30d=stats.verified_30d_count,
        accuracy_1d=stats.accuracy_1d,
        accuracy_7d=stats.accuracy_7d,
        accuracy_30d=stats.accuracy_30d,
        avg_return_1d=stats.avg_return_1d,
        avg_return_7d=stats.avg_return_7d,
        avg_return_30d=stats.avg_return_30d,
        is_unlocked=stats.is_unlocked,
        unlock_reason=stats.unlock_reason,
        last_updated=stats.calculated_at,
    )


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(db: Session = Depends(get_db)):
    """
    Check if system is unlocked for real trading.
    Returns current mode (observation/active) and reason.
    """
    unlocked, reason = is_system_unlocked(db)
    db_stats = get_latest_stats(db)

    # Build stats object
    stats = None
    if db_stats:
        stats = SimplifiedStats(
            total_predictions=db_stats.total_predictions,
            verified_1d=db_stats.verified_1d_count,
            verified_7d=db_stats.verified_7d_count,
            verified_30d=db_stats.verified_30d_count,
            accuracy_1d=db_stats.accuracy_1d,
            accuracy_7d=db_stats.accuracy_7d,
            accuracy_30d=db_stats.accuracy_30d,
            avg_return_1d=db_stats.avg_return_1d,
            avg_return_7d=db_stats.avg_return_7d,
            avg_return_30d=db_stats.avg_return_30d,
            is_unlocked=db_stats.is_unlocked,
            unlock_reason=db_stats.unlock_reason,
            last_updated=db_stats.calculated_at,
        )

    # Build unlock requirements
    current_predictions = db_stats.verified_7d_count if db_stats else 0
    current_accuracy = db_stats.accuracy_7d if db_stats else None

    unlock_requirements = UnlockRequirements(
        min_predictions=50,
        min_accuracy=55.0,
        current_predictions=current_predictions,
        current_accuracy=current_accuracy,
    )

    if unlocked:
        return SystemStatusResponse(
            is_unlocked=True,
            mode="active",
            message="✅ Systeem heeft voldoende accuracy bewezen. Je kunt de adviezen nu volgen.",
            stats=stats,
            unlock_requirements=unlock_requirements,
        )
    else:
        return SystemStatusResponse(
            is_unlocked=False,
            mode="observation",
            message="🔒 Observatiemodus: bekijk de adviezen, maar volg ze nog niet. Het systeem moet zichzelf eerst bewijzen.",
            stats=stats,
            unlock_requirements=unlock_requirements,
        )


@router.get("/predictions", response_model=list[PredictionResponse])
async def get_predictions(limit: int = 50, db: Session = Depends(get_db)):
    """
    Get recent predictions with their verification status.
    Shows whether each prediction was correct or not.
    """
    predictions = get_prediction_history(db, limit=limit)
    return predictions


@router.post("/run")
async def trigger_verification(db: Session = Depends(get_db)):
    """
    Manually trigger verification of pending predictions.
    Normally runs automatically via cron, but can be triggered manually.
    """
    try:
        results = run_verification(db)
        return {
            "status": "success",
            "verified_1d": results["verified_1d"],
            "verified_7d": results["verified_7d"],
            "verified_30d": results["verified_30d"],
            "errors": results["errors"][:5] if results["errors"] else [],  # Limit error output
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/recalculate")
async def recalculate_stats(db: Session = Depends(get_db)):
    """
    Recalculate verification statistics from all predictions.
    Use if stats seem out of sync.
    """
    try:
        stats = update_verification_stats(db)
        return {
            "status": "success",
            "accuracy_7d": stats.accuracy_7d,
            "is_unlocked": stats.is_unlocked,
            "unlock_reason": stats.unlock_reason,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recalculation failed: {str(e)}")
