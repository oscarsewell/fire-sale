"""Database interactions for the Discord bot"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Establishes a connection to the PostgreSQL database"""
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def insert_discord_user(discord_user_id username=None):
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
                (product_url, product_name, site_name, currency, page_exists),
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
