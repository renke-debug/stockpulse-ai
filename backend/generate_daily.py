#!/usr/bin/env python3
"""
Daily digest generation script.
Run via cron or GitHub Actions at 22:00 CET.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.models.database import init_db
from app.services.digest_generator import generate_digest


def main():
    print("=" * 50)
    print("StockPulse AI - Daily Digest Generator")
    print("=" * 50)

    print("\n1. Initializing database...")
    init_db()

    print("\n2. Generating digest (this may take a few minutes)...")
    try:
        result = generate_digest(save_to_db=True)

        print("\n" + "=" * 50)
        print("SUCCESS!")
        print("=" * 50)
        print(f"Date: {result['date']}")
        print(f"Generated at: {result['generated_at']}")
        print(f"Buy signals: {len(result['buy'])}")
        print(f"Sell signals: {len(result['sell'])}")

        if result['buy']:
            print("\nTop buy picks:")
            for pick in result['buy'][:3]:
                print(f"  - {pick['ticker']}: {pick['score']} ({pick['signal']})")

        if result['sell']:
            print("\nTop sell picks:")
            for pick in result['sell'][:3]:
                print(f"  - {pick['ticker']}: {pick['score']} ({pick['signal']})")

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
