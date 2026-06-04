"""Tests for the dashboard application login."""
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import bcrypt
import pytest
from streamlit.testing.v1 import AppTest

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_hashed(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _mock_db_row(
    user_id=1,
    username="testuser",
    email="test@example.com",
    is_verified=True,
    plain_password="password123",
):
    """Return a dict mimicking a psycopg2 RealDictRow for a joined user+password query."""
    return {
        "id": user_id,
        "username": username,
        "email": email,
        "is_verified": is_verified,
        "password_hash": _make_hashed(plain_password),
    }


# ── auth.hash_password ────────────────────────────────────────────────────────

def test_hash_password_returns_valid_bcrypt_hash():
    """hash_password should return a hash that bcrypt can verify."""
    from auth import hash_password
    hashed, salt = hash_password("mysecretpassword")
    assert bcrypt.checkpw("mysecretpassword".encode(), hashed.encode())
    assert len(salt) > 0


def test_hash_password_different_passwords_give_different_hashes():
    """Two different passwords should never produce the same hash."""
    from auth import hash_password
    hash1, _ = hash_password("password_one")
    hash2, _ = hash_password("password_two")
    assert hash1 != hash2


# ── auth.verify_password ──────────────────────────────────────────────────────

def test_verify_password_correct_password_returns_true():
    """verify_password should return True when the correct password is supplied."""
    from auth import verify_password
    salt = bcrypt.gensalt()
    stored = bcrypt.hashpw("correct_password".encode(), salt).decode()
    assert verify_password("correct_password", stored) is True


def test_verify_password_wrong_password_returns_false():
    """verify_password should return False for the wrong password."""
    from auth import verify_password
    salt = bcrypt.gensalt()
    stored = bcrypt.hashpw("correct_password".encode(), salt).decode()
    assert verify_password("wrong_password", stored) is False


# ── auth.register_user ────────────────────────────────────────────────────────

def test_register_user_success():
    """register_user should return user_id and verification_token on success."""
    from auth import register_user

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None  # no duplicate check hit
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    # First fetchone (duplicate check) returns None; second (RETURNING id) returns {"id": 42}
    mock_cursor.fetchone.side_effect = [None, {"id": 42}]

    with patch("auth.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__ = lambda s: mock_conn
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        result = register_user("newuser", "new@example.com", "securepass")

    assert result["user_id"] == 42
    assert "verification_token" in result
    assert len(result["verification_token"]) > 0


def test_register_user_duplicate_raises_value_error():
    """register_user should raise ValueError when username/email already exists."""
    from auth import register_user

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = {"id": 1}  # duplicate found
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("auth.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__ = lambda s: mock_conn
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(ValueError, match="already in use"):
            register_user("existinguser", "existing@example.com", "securepass")


# ── auth.login_user ───────────────────────────────────────────────────────────

def test_login_user_valid_credentials_returns_user_dict():
    """login_user should return a user dict for correct credentials on a verified account."""
    from auth import login_user

    row = _mock_db_row(plain_password="correctpass")

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = row
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("auth.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__ = lambda s: mock_conn
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        result = login_user("test@example.com", "correctpass")

    assert result["id"] == 1
    assert result["username"] == "testuser"
    assert result["email"] == "test@example.com"


def test_login_user_wrong_password_returns_none():
    """login_user should return None when the password is incorrect."""
    from auth import login_user

    row = _mock_db_row(plain_password="correctpass")

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = row
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("auth.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__ = lambda s: mock_conn
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        result = login_user("test@example.com", "wrongpass")

    assert result is None


def test_login_user_unknown_email_returns_none():
    """login_user should return None when no account exists for the given email."""
    from auth import login_user

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("auth.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__ = lambda s: mock_conn
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        result = login_user("nobody@example.com", "anypass")

    assert result is None


def test_login_user_unverified_account_raises_value_error():
    """login_user should raise ValueError when the account has not been verified."""
    from auth import login_user

    row = _mock_db_row(is_verified=False, plain_password="correctpass")

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = row
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("auth.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__ = lambda s: mock_conn
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(ValueError, match="not been verified"):
            login_user("test@example.com", "correctpass")


# ── auth.verify_email_token ───────────────────────────────────────────────────

def test_verify_email_token_valid_token_returns_true():
    """verify_email_token should return True and mark the token used for a valid token."""
    from auth import verify_email_token

    token_row = {
        "id": 10,
        "user_id": 1,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "used_at": None,
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = token_row
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("auth.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__ = lambda s: mock_conn
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        result = verify_email_token("valid_token_abc")

    assert result is True
    assert mock_cursor.execute.call_count == 3  # SELECT + 2x UPDATE


def test_verify_email_token_nonexistent_token_returns_false():
    """verify_email_token should return False when the token is not in the database."""
    from auth import verify_email_token

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("auth.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__ = lambda s: mock_conn
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        result = verify_email_token("nonexistent_token")

    assert result is False


def test_verify_email_token_already_used_returns_false():
    """verify_email_token should return False when the token has already been used."""
    from auth import verify_email_token

    token_row = {
        "id": 10,
        "user_id": 1,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "used_at": datetime.now(timezone.utc) - timedelta(minutes=5),
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = token_row
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("auth.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__ = lambda s: mock_conn
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        result = verify_email_token("already_used_token")

    assert result is False


def test_verify_email_token_expired_returns_false():
    """verify_email_token should return False when the token has expired."""
    from auth import verify_email_token

    token_row = {
        "id": 10,
        "user_id": 1,
        "expires_at": datetime.now(timezone.utc) - timedelta(hours=1),
        "used_at": None,
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = token_row
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("auth.get_db") as mock_get_db:
        mock_get_db.return_value.__enter__ = lambda s: mock_conn
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        result = verify_email_token("expired_token")

    assert result is False


# ── database.get_db_credentials ──────────────────────────────────────────────

def test_get_db_credentials_from_env_vars(monkeypatch):
    """get_db_credentials should return a dict when all env vars are set."""
    from database import get_db_credentials
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pass")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "testdb")

    creds = get_db_credentials()

    assert creds["host"] == "localhost"
    assert creds["port"] == 5432
    assert creds["username"] == "user"
    assert creds["password"] == "pass"
    assert creds["dbname"] == "testdb"


def test_get_db_credentials_missing_env_vars_raises(monkeypatch):
    """get_db_credentials should raise ValueError when env vars and secret ARN are absent."""
    from database import get_db_credentials
    for var in ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_PORT", "DB_NAME", "DB_SECRET_ARN"):
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(ValueError, match="Database credentials not found"):
        get_db_credentials()


def test_get_db_credentials_from_secrets_manager(monkeypatch):
    """get_db_credentials should fetch credentials from Secrets Manager when env vars are absent."""
    from database import get_db_credentials
    for var in ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_PORT", "DB_NAME"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv(
        "DB_SECRET_ARN", "arn:aws:secretsmanager:eu-west-2:123:secret:test")

    secret_payload = json.dumps({
        "host": "rds.example.com",
        "port": "5432",
        "username": "admin",
        "password": "secret",
        "dbname": "prod",
    })

    with patch("database.boto3.client") as mock_boto:
        mock_boto.return_value.get_secret_value.return_value = {
            "SecretString": secret_payload}
        creds = get_db_credentials()

    assert creds["host"] == "rds.example.com"
    assert creds["username"] == "admin"
    assert creds["dbname"] == "prod"


# ── database.get_db ───────────────────────────────────────────────────────────

def test_get_db_commits_on_success(monkeypatch):
    """get_db should commit the transaction when no exception is raised."""
    from database import get_db
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pass")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "testdb")

    mock_conn = MagicMock()
    with patch("database.psycopg2.connect", return_value=mock_conn):
        with get_db() as conn:
            assert conn is mock_conn
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


def test_get_db_rolls_back_on_error(monkeypatch):
    """get_db should roll back and re-raise when an exception occurs inside the block."""
    from database import get_db
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pass")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "testdb")

    mock_conn = MagicMock()
    with patch("database.psycopg2.connect", return_value=mock_conn):
        with pytest.raises(RuntimeError):
            with get_db():
                raise RuntimeError("query failed")
    mock_conn.rollback.assert_called_once()
    mock_conn.close.assert_called_once()


# ── ses_email.send_verification_email ────────────────────────────────────────

def test_send_verification_email_returns_true_on_success(monkeypatch):
    """send_verification_email should return True when SES accepts the request."""
    from ses_email import send_verification_email
    monkeypatch.setenv("AWS_REGION", "eu-west-2")
    monkeypatch.setenv("SES_FROM_EMAIL", "noreply@example.com")

    mock_ses = MagicMock()
    mock_ses.send_email.return_value = {"MessageId": "abc-123"}

    with patch("ses_email.boto3.client", return_value=mock_ses):
        result = send_verification_email(
            to_email="user@example.com",
            username="testuser",
            verification_token="mytoken",
            base_url="http://localhost:8501",
        )

    assert result is True
    mock_ses.send_email.assert_called_once()


def test_send_verification_email_returns_false_on_ses_error(monkeypatch):
    """send_verification_email should return False when SES raises an exception."""
    from ses_email import send_verification_email
    monkeypatch.setenv("AWS_REGION", "eu-west-2")
    monkeypatch.setenv("SES_FROM_EMAIL", "noreply@example.com")

    mock_ses = MagicMock()
    mock_ses.send_email.side_effect = Exception("SES error")

    with patch("ses_email.boto3.client", return_value=mock_ses):
        result = send_verification_email(
            to_email="user@example.com",
            username="testuser",
            verification_token="mytoken",
            base_url="http://localhost:8501",
        )

    assert result is False


def test_send_verification_email_builds_correct_link(monkeypatch):
    """send_verification_email should build the verification link from base_url and token."""
    from ses_email import send_verification_email
    monkeypatch.setenv("AWS_REGION", "eu-west-2")
    monkeypatch.setenv("SES_FROM_EMAIL", "noreply@example.com")

    mock_ses = MagicMock()
    mock_ses.send_email.return_value = {"MessageId": "abc-123"}

    with patch("ses_email.boto3.client", return_value=mock_ses):
        send_verification_email(
            to_email="user@example.com",
            username="testuser",
            verification_token="tok123",
            base_url="https://myhardwarehound.com",
        )

    call_kwargs = mock_ses.send_email.call_args
    body_text = call_kwargs[1]["Message"]["Body"]["Text"]["Data"]
    assert "https://myhardwarehound.com?verify_token=tok123" in body_text
