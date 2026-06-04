"""Database interactions for the Discord bot"""
import os
from datetime import datetime, timezone

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Establishes a connection to the PostgreSQL database"""
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def insert_discord_user(discord_user_id, username=None):
    """Creates or fetch a Discord user"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, discord)
                VALUES (%s, %s)
                ON CONFLICT (discord)
                DO UPDATE SET username = EXCLUDED.username
                RETURNING id
                """,
                (username or "Discord user", str(discord_user_id)),
            )
            return cursor.fetchone()[0]


def get_or_create_site(site_name):
    """Create or fetch a site"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO site_names (site)
                VALUES (%s)
                ON CONFLICT (site)
                DO UPDATE SET site = EXCLUDED.site
                RETURNING id
                """,
                (site_name,),
            )
            return cursor.fetchone()[0]


def get_or_create_product(product_url, product_name="Not set", site_name="Not set", currency="GBP", page_exists=True):
    """Create or fetch a product"""
    site_id = get_or_create_site(site_name)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO products (product_url, product_name, site_id, currency, page_exists)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (product_url)
                DO UPDATE SET 
                    product_name = EXCLUDED.product_name,
                    site_id = EXCLUDED.site_id,
                    currency = EXCLUDED.currency,
                    page_exists = EXCLUDED.page_exists
                RETURNING id
                """,
                (product_url, product_name, site_id, currency, page_exists),
            )
            return cursor.fetchone()[0]


def add_tracking(user_id, product_id, target_price, original_price=0):
    """Create or update a tracked product"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tracked_products (user_id, product_id, target_price, original_price)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, product_id)
                DO UPDATE SET
                    target_price = EXCLUDED.target_price,
                    original_price = EXCLUDED.original_price
                """,
                (user_id, product_id, target_price, original_price),
            )


def get_tracked_products(discord_user_id):
    """Retrieves tracked products for a Discord user"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.product_name,
                    p.product_url,
                    sn.site,
                    p.currency,
                    tp.target_price,
                    tp.original_price
                FROM tracked_products tp
                JOIN users u ON tp.user_id = u.id
                JOIN products p ON tp.product_id = p.id
                JOIN site_names sn ON p.site_id = sn.id
                WHERE u.discord = %s
                ORDER BY sn.site, p.product_name;
                """,
                (str(discord_user_id),),
            )
            rows = cursor.fetchall()

        return [
            {
                "product_id": row[0],
                "product_name": row[1],
                "product_url": row[2],
                "site_name": row[3],
                "currency": row[4],
                "target_price": row[5],
                "original_price": row[6],
            }
            for row in rows
        ]


def remove_tracking(discord_user_id, product_id):
    """Remove a tracked product for a user"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM tracked_products tp
                USING users u
                WHERE tp.user_id = u.id
                AND u.discord = %s
                AND tp.product_id = %s
                RETURNING tp.product_id
                """,
                (str(discord_user_id), product_id),
            )
            deleted_row = cursor.fetchone()

    return deleted_row is not None


def get_user_by_discord_id(discord_user_id):
    """Fetch a user record by their Discord ID"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, email, discord
                FROM users
                WHERE discord = %s
                """,
                (str(discord_user_id),),
            )
            row = cursor.fetchone()

    if row:
        return {
            "id": row[0],
            "username": row[1],
            "email": row[2],
            "discord": row[3],
        }
    return None


def add_price_history(product_id, current_price, scraped_at):
    """Insert scraped price data for a product."""
    if scraped_at is None:
        scraped_at = datetime.now(timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO price_history
                    (product_id, current_price, scraped_at)
                VALUES (%s, %s, %s)
                """,
                (product_id, current_price, scraped_at),
            )


def update_tracking_target_price(discord_user_id, product_id, new_target_price):
    """Update the target price for a tracked product"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE tracked_products tp
                SET target_price = %s
                FROM users u
                WHERE tp.user_id = u.id
                AND u.discord = %s
                AND tp.product_id = %s
                RETURNING tp.product_id
                """,
                (new_target_price, str(discord_user_id), product_id),
            )
            updated_row = cursor.fetchone()

    return updated_row is not None


def get_link_code(code):
    """Fetch a link code record"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, user_id, code, expires_at, used_at
                FROM discord_link_codes
                WHERE code = %s
                AND used_at IS NULL
                AND expires_at > NOW()
                """,
                (code,),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "user_id": row[1],
        "code": row[2],
        "expires_at": row[3],
        "used_at": row[4],
    }


def link_discord_account(code, discord_user_id):
    """Link a Discord account to a user using a link code"""
    link_code = get_link_code(code)
    if link_code is None:
        return None
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET discord = %s
                WHERE id = %s
                RETURNING id, username, email, discord
                """,
                (str(discord_user_id), link_code["user_id"]),
            )
            user_row = cursor.fetchone()

            cursor.execute(
                """
                UPDATE discord_link_codes
                SET used_at = NOW()
                WHERE id = %s
                """,
                (link_code["id"],),
            )

    return {
        "id": user_row[0],
        "username": user_row[1],
        "email": user_row[2],
        "discord": user_row[3],
    }
