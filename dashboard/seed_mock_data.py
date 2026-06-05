"""Seed mock price history data for the Corsair Vengeance 32GB DDR5 RAM product.

Run from the dashboard/ directory:
    python seed_mock_data.py [--user-id <id>]

The script is idempotent: re-running it will not create duplicate product/site
rows, but will append additional price_history rows.
"""

import argparse
from datetime import datetime, timedelta, timezone

from database import get_db

PRODUCT_URL = (
    "https://www.awd-it.co.uk/corsair-vengeance-32gb-2x16gb-ddr5-ram-5200mt-s-c40"
    "-memory-kit-black-cmk32gx5m2b5200z40.html"
)
PRODUCT_NAME = "Corsair Vengeance 32GB (2x16GB) DDR5 RAM 5200MT/s C40 Memory Kit Black"
SITE = "awd-it"
CURRENCY = "GBP"

# Prices in pence — 30 days of realistic variation around £349.99
# Target price: £319.99 (31999p), dips below it mid-way to trigger an alert scenario
PRICE_HISTORY_PENCE = [
    36999, 36999, 36499, 36499, 35999,  # days 1–5:  launch price drops
    35499, 35499, 34999, 34499, 34499,  # days 6–10: gradual fall
    # days 11–15: dips below target (£319.99)
    32999, 31999, 31999, 32499, 33499,
    34499, 34999, 34999, 35499, 35499,  # days 16–20: recovers
    35499, 34999, 34499, 34499, 33999,  # days 21–25: softens again
    34499, 34499, 34999, 34999, 34999,  # days 26–30: current window
]

ORIGINAL_PRICE_PENCE = PRICE_HISTORY_PENCE[0]
TARGET_PRICE_PENCE = 31999  # £319.99


def get_user_id_by_username(username: str) -> int:
    """Look up a user's ID by their username."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"No user found with username '{username}'")
            return row["id"]


def seed(user_id: int) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            # 1. Ensure site exists
            cur.execute(
                "INSERT INTO site_names (site) VALUES (%s) ON CONFLICT (site) DO NOTHING",
                (SITE,),
            )
            cur.execute("SELECT id FROM site_names WHERE site = %s", (SITE,))
            site_id = cur.fetchone()["id"]
            print(f"Site '{SITE}' → id={site_id}")

            # 2. Upsert product
            cur.execute(
                """
                INSERT INTO products (product_url, product_name, site_id, currency)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (product_url) DO UPDATE SET product_name = EXCLUDED.product_name
                RETURNING id
                """,
                (PRODUCT_URL, PRODUCT_NAME, site_id, CURRENCY),
            )
            product_id = cur.fetchone()["id"]
            print(f"Product '{PRODUCT_NAME}' → id={product_id}")

            # 3. Ensure tracked_products row exists for the given user
            cur.execute(
                """
                INSERT INTO tracked_products (user_id, product_id, target_price, original_price)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, product_id) DO NOTHING
                """,
                (user_id, product_id, TARGET_PRICE_PENCE, ORIGINAL_PRICE_PENCE),
            )
            print(f"Tracked product ensured for user_id={user_id}")

            # 4. Insert price history (one entry per day, going back 30 days)
            now = datetime.now(tz=timezone.utc)
            days_back = len(PRICE_HISTORY_PENCE) - 1
            rows = [
                (product_id, price, now - timedelta(days=days_back - i))
                for i, price in enumerate(PRICE_HISTORY_PENCE)
            ]
            cur.executemany(
                "INSERT INTO price_history (product_id, current_price, scraped_at) VALUES (%s, %s, %s)",
                rows,
            )
            print(f"Inserted {len(rows)} price history rows")

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed mock price history data.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--username", type=str, default="Tomm0",
        help="Username to attach the tracked product to (default: Tomm0)"
    )
    group.add_argument(
        "--user-id", type=int,
        help="User ID to attach the tracked product to (overrides --username)"
    )
    args = parser.parse_args()
    if args.user_id:
        uid = args.user_id
    else:
        uid = get_user_id_by_username(args.username)
        print(f"Resolved username '{args.username}' → user_id={uid}")
    seed(uid)
