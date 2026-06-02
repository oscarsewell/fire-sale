"""Database layer for the Fire Sale dashboard.

Credentials are resolved in priority order:
  1. Individual env vars: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
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

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def _get_credentials() -> dict:
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME")

    if all([host, user, password, dbname]):
        return {
            "host": host,
            "port": int(port),
            "user": user,
            "password": password,
            "dbname": dbname,
        }

    secret_arn = os.getenv("DB_SECRET_ARN")
    if not secret_arn:
        raise EnvironmentError(
            "Provide DB_HOST/DB_USER/DB_PASSWORD/DB_NAME/DB_PORT "
            "or set DB_SECRET_ARN for AWS Secrets Manager."
        )

    region = os.getenv("AWS_REGION", "eu-west-2")
    client = boto3.client("secretsmanager", region_name=region)
    resp = client.get_secret_value(SecretId=secret_arn)
    creds = json.loads(resp["SecretString"])
    return {
        "host": creds["host"],
        "port": int(creds.get("port", 5432)),
        "user": creds["username"],
        "password": creds["password"],
        "dbname": creds["dbname"],
    }


@contextmanager
def get_db():
    """Yield a psycopg2 connection; commit on success, rollback on error."""
    creds = _get_credentials()
    conn = psycopg2.connect(
        cursor_factory=psycopg2.extras.RealDictCursor, **creds
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
