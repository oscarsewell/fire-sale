"""Database layer for the Fire Sale dashboard.

Credentials are resolved in priority order:
  1. Individual env vars: DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, DB_NAME
  2. AWS Secrets Manager via DB_SECRET_ARN
"""
import json
import logging
import os
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

import boto3
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

secrets_client = boto3.client("secretsmanager")


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def _get_credentials() -> dict:
    """Retrieve database credentials from environment or AWS Secrets Manager.

    First attempts to load from environment variables (set via .env or ECS env).
    Falls back to AWS Secrets Manager if environment variables are not found.
    """
    # Resolve .env relative to this file so it works regardless of cwd
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)

    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")

    # If all env vars are present, use them
    if all([host, user, password, port, dbname]):
        logger.info("Using credentials from environment variables")
        return {
            "host": host,
            "port": int(port),
            "username": user,
            "password": password,
            "dbname": dbname,
        }

    # Otherwise, fall back to AWS Secrets Manager (ECS / production)
    try:
        secret_arn = os.getenv("DB_SECRET_ARN")
        if not secret_arn:
            raise ValueError(
                "DB_SECRET_ARN not set and environment variables incomplete. "
                "Either set DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, DB_NAME "
                "or set DB_SECRET_ARN for AWS Secrets Manager."
            )

        logger.info("Using credentials from AWS Secrets Manager")
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        credentials = json.loads(response["SecretString"])

        password_from_secret = credentials.get("password")
        if not password_from_secret and credentials.get("password_secret_arn"):
            password_resp = secrets_client.get_secret_value(
                SecretId=credentials["password_secret_arn"]
            )
            password_obj = json.loads(password_resp["SecretString"])
            password_from_secret = password_obj.get("password")

        if not password_from_secret:
            raise ValueError(
                "Database password not found in Secrets Manager payload")

        return {
            "host": credentials.get("host"),
            "port": int(credentials.get("port", 5432)),
            "username": credentials.get("username"),
            "password": password_from_secret,
            "dbname": credentials.get("dbname"),
        }
    except Exception as e:
        logger.error("Failed to retrieve database credentials: %s", str(e))
        raise


@contextmanager
def get_db():
    """Yield a psycopg2 connection; commit on success, rollback on error."""
    creds = _get_credentials()
    conn = psycopg2.connect(
        host=creds["host"],
        port=creds["port"],
        user=creds["username"],
        password=creds["password"],
        database=creds["dbname"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# User queries
# ---------------------------------------------------------------------------

def create_user(username: str, email: str) -> int:
    """Insert a new unverified user; returns the new user's id."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, email, is_verified)
                VALUES (%s, %s, FALSE)
                RETURNING id
                """,
                (username, email),
            )
            return cur.fetchone()["id"]


def save_password(user_id: int, password_hash: str, salt: str) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO passwords (user_id, password_hash, salt) VALUES (%s, %s, %s)",
                (user_id, password_hash, salt),
            )


def get_user_by_email(email: str) -> Optional[dict]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[dict]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def email_exists(email: str) -> bool:
    return get_user_by_email(email) is not None


def username_exists(username: str) -> bool:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            return cur.fetchone() is not None


def get_password_record(user_id: int) -> Optional[dict]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM passwords WHERE user_id = %s", (user_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None


# ---------------------------------------------------------------------------
# Email verification token queries
# ---------------------------------------------------------------------------

def create_verification_token(user_id: int) -> str:
    """Generate, persist, and return a 32-byte URL-safe verification token."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    with get_db() as conn:
        with conn.cursor() as cur:
            # Invalidate any pending tokens so old links stop working
            cur.execute(
                "DELETE FROM email_verification_tokens WHERE user_id = %s AND used_at IS NULL",
                (user_id,),
            )
            cur.execute(
                """
                INSERT INTO email_verification_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, token, expires_at),
            )
    return token


def consume_verification_token(token: str) -> Optional[int]:
    """
    Validate a verification token.
    If valid: marks it as used, marks the user as verified, returns user_id.
    If invalid / expired / already used: returns None.
    """
    now = datetime.now(timezone.utc)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, expires_at, used_at FROM email_verification_tokens WHERE token = %s",
                (token,),
            )
            row = cur.fetchone()
            if row is None or row["used_at"] is not None:
                return None

            expires = row["expires_at"]
            # Ensure timezone-aware comparison
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < now:
                return None

            cur.execute(
                "UPDATE email_verification_tokens SET used_at = %s WHERE token = %s",
                (now, token),
            )
            cur.execute(
                "UPDATE users SET is_verified = TRUE WHERE id = %s",
                (row["user_id"],),
            )
    return row["user_id"]


# ---------------------------------------------------------------------------
# Tracked products queries
# ---------------------------------------------------------------------------

def get_tracked_products_for_user(user_id: int) -> list:
    """Return all tracked products with the latest price for a given user."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    tp.id            AS tracking_id,
                    tp.target_price,
                    tp.original_price,
                    p.product_name,
                    p.product_url,
                    p.currency,
                    p.page_exists,
                    s.site           AS site_name,
                    (
                        SELECT ph.current_price
                        FROM price_history ph
                        WHERE ph.product_id = p.id
                        ORDER BY ph.scraped_at DESC
                        LIMIT 1
                    ) AS latest_price
                FROM tracked_products tp
                JOIN products p ON p.id = tp.product_id
                JOIN site_names s ON s.id = p.site_id
                WHERE tp.user_id = %s
                ORDER BY p.product_name
                """,
                (user_id,),
            )
            return [dict(row) for row in cur.fetchall()]
