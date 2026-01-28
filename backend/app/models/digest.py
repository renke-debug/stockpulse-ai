from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.models.database import Base


class Digest(Base):
    """Daily digest with top 5 buy/sell recommendations."""

    __tablename__ = "digests"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), unique=True, index=True, nullable=False)  # YYYY-MM-DD
    generated_at = Column(DateTime, server_default=func.now())
    data = Column(JSON, nullable=False)
    # data structure:
    # {
    #   "buy": [{"ticker": "AAPL", "name": "Apple", "score": 85, "explanation": "..."}],
    #   "sell": [{"ticker": "XYZ", "name": "...", "score": -72, "explanation": "..."}]
    # }

    def __repr__(self) -> str:
        return f"<Digest {self.date}>"
