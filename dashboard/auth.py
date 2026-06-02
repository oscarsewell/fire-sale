"""Authentication logic for Hardware Hound."""
import logging
import secrets
from datetime import datetime, timedelta

import bcrypt

from database import get_db

logger = logging.getLogger(__name__)


def hash_password(plain_password: str) -> tuple[str, str]:
    """Hash a password with bcrypt. Returns (password_hash, salt) as UTF-8 strings."""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return password_hash.decode("utf-8"), salt.decode("utf-8")


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Check a plain-text password against a stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        stored_hash.encode("utf-8"),
    )


def register_user(username: str, email: str, plain_password: str) -> dict:
    """Create a new unverified user account.

    Returns a dict with 'user_id' and 'verification_token'.
    Raises ValueError if the username or email is already in use.
    """
    logger.info(
        "Attempting to register new user: username=%s, email=%s", username, email)
    password_hash, salt = hash_password(plain_password)
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM users WHERE username = %s OR email = %s",
                    (username, email),
                )
                if cur.fetchone():
                    logger.warning(
                        "Registration failed – username or email already in use: %s / %s", username, email)
                    raise ValueError("Username or email is already in use.")

                cur.execute(
                    "INSERT INTO users (username, email, is_verified) "
                    "VALUES (%s, %s, FALSE) RETURNING id",
                    (username, email),
                )
                user_id = cur.fetchone()["id"]
                logger.debug("Inserted user row with id=%s", user_id)

                cur.execute(
                    "INSERT INTO passwords (user_id, password_hash, salt) "
                    "VALUES (%s, %s, %s)",
                    (user_id, password_hash, salt),
                )
                logger.debug("Inserted password row for user_id=%s", user_id)

                cur.execute(
                    "INSERT INTO email_verification_tokens (user_id, token, expires_at) "
                    "VALUES (%s, %s, %s)",
                    (user_id, token, expires_at),
                )
                logger.debug(
                    "Inserted verification token for user_id=%s, expires_at=%s", user_id, expires_at)
    except ValueError:
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error during registration for %s: %s", email, exc)
        raise

    logger.info(
        "User registered successfully: user_id=%s, email=%s", user_id, email)
    return {"user_id": user_id, "verification_token": token}


def login_user(email: str, plain_password: str) -> dict | None:
    """Authenticate a user by email and password.

    Returns a user dict on success, None if credentials are wrong.
    Raises ValueError if the account has not been verified yet.
    """
    logger.info("Login attempt for email=%s", email)
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT u.id, u.username, u.email, u.is_verified, p.password_hash
                    FROM users u
                    JOIN passwords p ON p.user_id = u.id
                    WHERE u.email = %s
                    """,
                    (email,),
                )
                row = cur.fetchone()
    except Exception as exc:
        logger.error("DB error during login for email=%s: %s", email, exc)
        raise

    if row is None:
        logger.warning("Login failed – no account found for email=%s", email)
        return None

    if not verify_password(plain_password, row["password_hash"]):
        logger.warning("Login failed – incorrect password for email=%s", email)
        return None

    if not row["is_verified"]:
        logger.warning(
            "Login blocked – account not verified for email=%s", email)
        raise ValueError(
            "Your account has not been verified yet. "
            "Please check your email for a verification link."
        )

    logger.info("Login successful for user_id=%s, email=%s", row["id"], email)
    return {
        "id": int(row["id"]),
        "username": str(row["username"]),
        "email": str(row["email"]),
    }


def verify_email_token(token: str) -> bool:
    """Validate an email verification token and mark the user as verified.

    Returns True on success, False if the token is missing, already used, or expired.
    """
    logger.info("Processing email verification token")
    now = datetime.utcnow()

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, user_id, expires_at, used_at "
                    "FROM email_verification_tokens WHERE token = %s",
                    (token,),
                )
                row = cur.fetchone()

                if row is None:
                    logger.warning("Verification failed – token not found")
                    return False

                if row["used_at"] is not None:
                    logger.warning(
                        "Verification failed – token already used (user_id=%s, used_at=%s)", row["user_id"], row["used_at"])
                    return False

                if row["expires_at"] < now:
                    logger.warning(
                        "Verification failed – token expired (user_id=%s, expired_at=%s)", row["user_id"], row["expires_at"])
                    return False

                cur.execute(
                    "UPDATE email_verification_tokens SET used_at = %s WHERE id = %s",
                    (now, row["id"]),
                )
                cur.execute(
                    "UPDATE users SET is_verified = TRUE WHERE id = %s",
                    (row["user_id"],),
                )
                logger.info(
                    "Email verified successfully for user_id=%s", row["user_id"])
    except Exception as exc:
        logger.error("DB error during email verification: %s", exc)
        raise

    return True
