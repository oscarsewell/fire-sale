"""Tests for the insertion module."""
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock
import pytest
import psycopg2

from insertion import insert_product_into_db, get_db_credentials


def test_get_db_credentials(monkeypatch):
    """Test that get_db_credentials returns credentials from environment variables."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pass")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "db")

    credentials = get_db_credentials()
    assert credentials == {
        "host": "localhost",
        "port": 5432,
        "username": "user",
        "password": "pass",
        "dbname": "db",
    }


def test_get_db_credentials_missing_env_vars(monkeypatch):
    """Test that get_db_credentials raises an exception when environment variables are missing."""
    # Clear environment variables
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)

    with pytest.raises(ValueError):
        get_db_credentials()


def test_insert_product_into_db_valid_input():
    """Tests that a valid product is inserted into the database."""
    mock_connection = Mock()
    mock_cursor = MagicMock()

    # Set up the context manager properly
    mock_connection.cursor.return_value.__enter__ = Mock(
        return_value=mock_cursor)
    mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)

    product = {
        "product_id": "123",
        "product_name": "Apple iPhone 13 Pro Max",
        "original_price": 109900,
        "current_price": 99900,
        "currency_code": "USD",
        "url": "https://www.example.com/product/123",
        "website_name": "ExampleStore",
        "scraped_at": datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(0)))
    }

    insert_product_into_db(product, mock_connection)

    mock_connection.cursor.assert_called_once()
    expected_query = """
                INSERT INTO price_history (product_id, current_price, original_price, scraped_at)
                VALUES (%s, %s, %s, %s)
            """
    mock_cursor.execute.assert_called_once_with(
        expected_query,
        ("123", 99900, 109900, product["scraped_at"])
    )
    mock_connection.commit.assert_called_once()


def test_insert_product_into_db_non_dict_raises_error():
    """Tests that a non-dictionary product raises a TypeError."""
    mock_connection = Mock()

    with pytest.raises(TypeError):
        insert_product_into_db("not a dict", mock_connection)

    with pytest.raises(TypeError):
        insert_product_into_db(None, mock_connection)

    with pytest.raises(TypeError):
        insert_product_into_db(123, mock_connection)


def test_insert_product_into_db_missing_keys_raises_error():
    """Tests that a product missing required keys raises a ValueError."""
    mock_connection = Mock()

    incomplete_product = {
        "product_id": "123",
        "product_name": "iPhone",
        "original_price": 109900,
    }

    with pytest.raises(ValueError, match="missing required keys"):
        insert_product_into_db(incomplete_product, mock_connection)

    # Should not attempt any database operations
    mock_connection.cursor.assert_not_called()


def test_insert_product_into_db_database_error_rolls_back():
    """Tests that database errors trigger a rollback."""
    mock_connection = Mock()
    mock_cursor = MagicMock()

    # Set up the context manager properly
    mock_connection.cursor.return_value.__enter__ = Mock(
        return_value=mock_cursor)
    mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)

    # Make cursor.execute raise a DatabaseError
    mock_cursor.execute.side_effect = psycopg2.DatabaseError(
        "Connection failed")

    product = {
        "product_id": "123",
        "product_name": "Apple iPhone 13 Pro Max",
        "original_price": 109900,
        "current_price": 99900,
        "currency_code": "USD",
        "url": "https://www.example.com/product/123",
        "website_name": "ExampleStore",
        "scraped_at": datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(0)))
    }

    with pytest.raises(psycopg2.DatabaseError):
        insert_product_into_db(product, mock_connection)

    mock_connection.rollback.assert_called_once()
    mock_connection.commit.assert_not_called()


def test_insert_product_into_db_all_required_keys():
    """Tests that all required keys must be present for successful insertion."""
    mock_connection = Mock()

    required_keys = (
        "product_name", "product_id", "original_price",
        "current_price", "currency_code", "url", "website_name", "scraped_at"
    )

    # Test each missing key individually
    for missing_key in required_keys:
        product = {
            "product_id": "123",
            "product_name": "iPhone",
            "original_price": 109900,
            "current_price": 99900,
            "currency_code": "USD",
            "url": "https://www.example.com/product/123",
            "website_name": "ExampleStore",
            "scraped_at": datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(0)))
        }
        del product[missing_key]

        with pytest.raises(ValueError, match="missing required keys"):
            insert_product_into_db(product, mock_connection)
