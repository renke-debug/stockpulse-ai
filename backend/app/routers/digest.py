from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import date

from app.models.database import get_db
from app.services.digest_generator import get_latest_digest, get_digest_by_date, generate_digest

router = APIRouter()


@router.get("/latest")
async def get_latest(db: Session = Depends(get_db)):
    """Get the most recent daily digest."""
    digest = get_latest_digest(db)

    if digest is None:
        return {
            "date": str(date.today()),
            "generated_at": None,
            "buy": [],
            "sell": [],
            "message": "No digest available yet. Generate one first.",
        }

    return digest


@router.get("/{digest_date}")
async def get_by_date(digest_date: str, db: Session = Depends(get_db)):
    """Get digest for a specific date (YYYY-MM-DD format)."""
    try:
        parsed_date = date.fromisoformat(digest_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    digest = get_digest_by_date(db, str(parsed_date))

    if digest is None:
        raise HTTPException(status_code=404, detail=f"No digest found for {digest_date}")

    return digest


@router.post("/generate")
async def trigger_generation(db: Session = Depends(get_db)):
    """
    Manually trigger digest generation.
    Note: This can take a few minutes to complete.
    """
    try:
        result = generate_digest(db=db, save_to_db=True)
        return {
            "status": "success",
            "date": result["date"],
            "buy_count": len(result["buy"]),
            "sell_count": len(result["sell"]),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Digest generation failed: {str(e)}")
