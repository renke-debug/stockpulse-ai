from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.models.database import Base


class User(Base):
    """User accounts with budget configuration."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    budget = Column(Float, nullable=False, default=10000.0)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<User {self.email}>"
