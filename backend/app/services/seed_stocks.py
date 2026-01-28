"""
Seed script to populate the stocks table from SP100 JSON file.
"""

import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.models.database import SessionLocal, init_db
from app.models.stock import Stock


def seed_stocks(db: Session, json_path: str = "data/stocks_sp100.json") -> int:
    """
    Seed the stocks table from JSON file.

    Args:
        db: Database session
        json_path: Path to JSON file with stock data

    Returns:
        Number of stocks added
    """
    # Read JSON file
    file_path = Path(__file__).parent.parent.parent / json_path
    with open(file_path, "r") as f:
        stocks_data = json.load(f)

    added = 0
    for stock_data in stocks_data:
        # Check if stock already exists
        existing = db.query(Stock).filter(Stock.ticker == stock_data["ticker"]).first()
        if existing:
            continue

        stock = Stock(
            ticker=stock_data["ticker"],
            name=stock_data["name"],
            sector=stock_data.get("sector"),
        )
        db.add(stock)
        added += 1

    db.commit()
    return added


def main():
    """Run seed script."""
    print("Initializing database...")
    init_db()

    print("Seeding stocks...")
    db = SessionLocal()
    try:
        count = seed_stocks(db)
        print(f"Added {count} stocks to database.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
