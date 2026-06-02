"""Authentication logic for the Fire Sale dashboard.

Handles registration, login, email verification, and Streamlit session state.
Passwords are hashed with bcrypt; the bcrypt output (which embeds the salt)
is stored in `password_hash` and the raw salt is stored in `salt` to satisfy
the existing schema.
"""
import re
from typing import Optional, Tuple

import bcrypt
import streamlit as st

import db


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def _hash_password(plain: str) -> Tuple[str, str]:
    """Return (password_hash, salt) as decoded strings."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8"), salt.decode("utf-8")


def _check_password(plain: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_registration(
    username: str,
    email: str,
    password: str,
    confirm: str,
) -> Optional[str]:
    """
    Return an error message string if validation fails, or None if valid.
    Checks are ordered so the most actionable error is shown first.
    """
    if not _USERNAME_RE.match(username):
        return "Username must be 3–30 characters and contain only letters, numbers, or underscores."
    if not _EMAIL_RE.match(email):
        return "Please enter a valid email address."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", password):
        return "Password must contain at least one special character."
    if password != confirm:
        return "Passwords do not match."
    return None


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_user(
    username: str,
    email: str,
    password: str,
    app_url: str,
) -> Tuple[bool, str]:
    """
    Create a new user account and send a verification email.

    Returns (success: bool, message: str).
    """
    from email_service import send_verification_email

    # Check uniqueness
    if db.username_exists(username):
        return False, "That username is already taken."

    existing = db.get_user_by_email(email)
    if existing:
        if not existing["is_verified"]:
            # Resend verification rather than blocking with a cryptic error
            token = db.create_verification_token(existing["id"])
            send_verification_email(email, token, app_url)
            return (
                False,
                "An account with that email already exists but hasn't been verified. "
                "We've resent the verification email — please check your inbox.",
            )
        return False, "An account with that email address already exists."

    password_hash, salt = _hash_password(password)

    try:
        user_id = db.create_user(username, email)
        db.save_password(user_id, password_hash, salt)
        token = db.create_verification_token(user_id)
        send_verification_email(email, token, app_url)
    except Exception as exc:
        return False, f"Registration failed: {exc}"

    return True, "Account created! Check your inbox for a verification email."


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def login_user(email: str, password: str) -> Tuple[bool, str]:
    """
    Validate credentials and populate st.session_state on success.

    Returns (success: bool, message: str).
    """
    user = db.get_user_by_email(email)
    if user is None:
        return False, "Invalid email or password."

    pwd_record = db.get_password_record(user["id"])
    if pwd_record is None or not _check_password(password, pwd_record["password_hash"]):
        return False, "Invalid email or password."

    if not user["is_verified"]:
        return False, "EMAIL_NOT_VERIFIED"

    _set_session(user)
    return True, f"Welcome back, {user['username']}!"


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------

def verify_email(token: str) -> Tuple[bool, str]:
    """
    Consume a verification token.
    Returns (success: bool, message: str).
    """
    user_id = db.consume_verification_token(token)
    if user_id is None:
        return False, "This verification link is invalid or has expired."
    return True, "Email verified! You can now log in."


def resend_verification(email: str, app_url: str) -> Tuple[bool, str]:
    """Re-generate and resend a verification email for an unverified account."""
    from email_service import send_verification_email

    user = db.get_user_by_email(email)
    if user is None:
        # Don't reveal whether the address exists
        return True, "If that email is registered, a new verification link has been sent."
    if user["is_verified"]:
        return False, "That account is already verified. Please log in."

    token = db.create_verification_token(user["id"])
    send_verification_email(email, token, app_url)
    return True, "A new verification email has been sent."


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _set_session(user: dict) -> None:
    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    st.session_state["email"] = user["email"]
    st.session_state["discord"] = user.get("discord")


def is_authenticated() -> bool:
    return "user_id" in st.session_state


def get_current_user() -> Optional[dict]:
    if not is_authenticated():
        return None
    return {
        "user_id": st.session_state["user_id"],
        "username": st.session_state["username"],
        "email": st.session_state["email"],
        "discord": st.session_state.get("discord"),
    }


def logout() -> None:
    for key in ("user_id", "username", "email", "discord"):
        st.session_state.pop(key, None)
