"""Database interactions for the Discord bot"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Establishes a connection to the PostgreSQL database"""
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def insert_discord_user(discord_user_id):
    """Creates or fetch a Discord user"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (notification_destination, user_contact)
                VALUES (%s, %s)
                ON CONFLICT (user_contact)
                DO UPDATE SET notification_destination = EXCLUDED.notification_destination
                RETURNING id
                """,
                ("discord", str(discord_user_id)),
            )
            return cursor.fetchone()[0]


def get_or_create_product(product_url, product_name, site_name, currency="GBP"):
    """Create or fetch a product"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO products (product_url, product_name, site_name, currency)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (product_url)
                DO UPDATE SET site_name = EXCLUDED.site_name
                RETURNING id
                """,
                (product_url, product_name, site_name, currency),
            )
            return cursor.fetchone()[0]


def add_tracking(user_id, product_id, target_discount):
    """Create or update a tracked product"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tracked_products (user_id, product_id, target_discount)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, product_id)
                DO UPDATE SET target_discount = EXCLUDED.target_discount
                """,
                (user_id, product_id, target_discount),
            )
