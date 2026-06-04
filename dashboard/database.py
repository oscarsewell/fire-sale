"""Database connection helper for Hardware Hound."""
import json
import logging
import os
from contextlib import contextmanager

import boto3
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_db_credentials() -> dict:
    """Load DB credentials from env vars, falling back to AWS Secrets Manager."""
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")

    if all([host, user, password, port, dbname]):
        logger.debug(
            "DB credentials loaded from environment variables (host=%s, dbname=%s)", host, dbname)
        return {
            "host": host,
            "port": int(port),
            "username": user,
            "password": password,
            "dbname": dbname,
        }

    secret_arn = os.getenv("DB_SECRET_ARN")
    if not secret_arn:
        logger.error(
            "DB credentials missing: no env vars and no DB_SECRET_ARN set. "
            "Set DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, DB_NAME or DB_SECRET_ARN."
        )
        raise ValueError(
            "Database credentials not found. Set DB_HOST, DB_USER, DB_PASSWORD, "
            "DB_PORT, DB_NAME or set DB_SECRET_ARN for AWS Secrets Manager."
        )

    logger.info(
        "Fetching DB credentials from Secrets Manager (arn=%s)", secret_arn)
    try:
        response = boto3.client(
            "secretsmanager").get_secret_value(SecretId=secret_arn)
    except Exception as exc:
        logger.error("Failed to retrieve secret from Secrets Manager: %s", exc)
        raise
    credentials = json.loads(response["SecretString"])
    logger.debug("DB credentials loaded from Secrets Manager")
    return {
        "host": credentials["host"],
        "port": int(credentials.get("port", 5432)),
        "username": credentials["username"],
        "password": credentials["password"],
        "dbname": credentials["dbname"],
    }


@contextmanager
def get_db():
    """Context manager yielding a psycopg2 connection.

    Commits on success, rolls back on error, and always closes the connection.
    """
    creds = get_db_credentials()
    logger.debug("Opening DB connection to %s:%s/%s",
                 creds["host"], creds["port"], creds["dbname"])
    try:
        conn = psycopg2.connect(
            host=creds["host"],
            port=creds["port"],
            user=creds["username"],
            password=creds["password"],
            dbname=creds["dbname"],
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    except psycopg2.OperationalError as exc:
        logger.error("Could not connect to database: %s", exc)
        raise
    try:
        yield conn
        conn.commit()
        logger.debug("DB transaction committed")
    except Exception as exc:
        conn.rollback()
        logger.error("DB transaction rolled back due to error: %s", exc)
        raise
    finally:
        conn.close()
        logger.debug("DB connection closed")


def upsert_product(url: str, product_name: str, site: str, currency: str) -> int:
    """Insert a product if it doesn't exist, or return the existing id."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO site_names (site) VALUES (%s) ON CONFLICT (site) DO NOTHING",
                (site,),
            )
            cur.execute("SELECT id FROM site_names WHERE site = %s", (site,))
            site_id = cur.fetchone()["id"]

            cur.execute(
                """
                INSERT INTO products (product_url, product_name, site_id, currency)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (product_url) DO UPDATE SET product_name = EXCLUDED.product_name
                RETURNING id
                """,
                (url, product_name, site_id, currency),
            )
            return cur.fetchone()["id"]


def add_tracked_product(user_id: int, product_id: int, target_price: int, original_price: int) -> None:
    """Insert a row into tracked_products. Raises ValueError if already tracked."""
    with get_db() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO tracked_products (user_id, product_id, target_price, original_price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (user_id, product_id, target_price, original_price),
                )
            except psycopg2.errors.UniqueViolation:
                raise ValueError("You are already tracking this product.")


def get_tracked_products(user_id: int) -> list[dict]:
    """Return all tracked products for a user with current price and product details."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.id AS product_id,
                    p.product_name,
                    p.product_url,
                    s.site,
                    p.currency,
                    tp.target_price,
                    tp.original_price,
                    (
                        SELECT ph.current_price
                        FROM price_history ph
                        WHERE ph.product_id = p.id
                        ORDER BY ph.scraped_at DESC
                        LIMIT 1
                    ) AS current_price
                FROM tracked_products tp
                JOIN products p ON p.id = tp.product_id
                JOIN site_names s ON s.id = p.site_id
                WHERE tp.user_id = %s
                ORDER BY p.product_name
                """,
                (user_id,),
            )
            return cur.fetchall()


def remove_tracked_product(user_id: int, product_id: int) -> None:
    """Delete a row from tracked_products for the given user and product."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM tracked_products WHERE user_id = %s AND product_id = %s",
                (user_id, product_id),
            )
