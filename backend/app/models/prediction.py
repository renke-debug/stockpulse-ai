"""
Prediction tracking model.
Logs every advice and tracks actual outcomes for verification.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from app.models.database import Base
import enum


class PredictionDirection(str, enum.Enum):
    BUY = "buy"  # Expecting price to go up
    SELL = "sell"  # Expecting price to go down


class Prediction(Base):
    """
    Tracks each prediction/advice and its outcome.
    Used for self-verification before trusting the system.
    """

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)

    # What was predicted
    ticker = Column(String(10), index=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    direction = Column(String(10), nullable=False)  # "buy" or "sell"
    score = Column(Float, nullable=False)  # Original score (-100 to +100)

    # Price at time of prediction
    prediction_date = Column(DateTime, server_default=func.now(), index=True)
    price_at_prediction = Column(Float, nullable=False)

    # Verification after 1 day
    price_after_1d = Column(Float, nullable=True)
    verified_1d = Column(Boolean, default=False)
    correct_1d = Column(Boolean, nullable=True)  # Was direction correct?
    return_1d = Column(Float, nullable=True)  # % return

    # Verification after 7 days
    price_after_7d = Column(Float, nullable=True)
    verified_7d = Column(Boolean, default=False)
    correct_7d = Column(Boolean, nullable=True)
    return_7d = Column(Float, nullable=True)

    # Verification after 30 days
    price_after_30d = Column(Float, nullable=True)
    verified_30d = Column(Boolean, default=False)
    correct_30d = Column(Boolean, nullable=True)
    return_30d = Column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<Prediction {self.ticker} {self.direction} @ {self.prediction_date}>"


class VerificationStats(Base):
    """
    Aggregated verification statistics.
    Updated daily after verification runs.
    """

    __tablename__ = "verification_stats"

    id = Column(Integer, primary_key=True, index=True)
    calculated_at = Column(DateTime, server_default=func.now())

    # Total predictions
    total_predictions = Column(Integer, default=0)

    # 1-day accuracy
    verified_1d_count = Column(Integer, default=0)
    correct_1d_count = Column(Integer, default=0)
    accuracy_1d = Column(Float, nullable=True)  # Percentage
    avg_return_1d = Column(Float, nullable=True)

    # 7-day accuracy
    verified_7d_count = Column(Integer, default=0)
    correct_7d_count = Column(Integer, default=0)
    accuracy_7d = Column(Float, nullable=True)
    avg_return_7d = Column(Float, nullable=True)

    # 30-day accuracy
    verified_30d_count = Column(Integer, default=0)
    correct_30d_count = Column(Integer, default=0)
    accuracy_30d = Column(Float, nullable=True)
    avg_return_30d = Column(Float, nullable=True)

    # Hypothetical portfolio performance
    hypothetical_return_total = Column(Float, nullable=True)  # If you followed all advice

    # System status
    is_unlocked = Column(Boolean, default=False)  # True when accuracy > 55% and 50+ predictions
    unlock_reason = Column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<VerificationStats {self.calculated_at} acc={self.accuracy_7d}%>"
