"""Tests for the insertion module."""
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch
import pytest
import psycopg2

from insertion import insert_product_into_db, get_db_credentials, mark_products_defunct
from lambda_handler import lambda_handler


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
        "current_price": 99900,
        "scraped_at": datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(0)))
    }

    insert_product_into_db(product, mock_connection)

    mock_connection.cursor.assert_called_once()
    expected_query = """
                INSERT INTO price_history (product_id, current_price, scraped_at)
                VALUES (%s, %s, %s)
            """
    mock_cursor.execute.assert_called_once_with(
        expected_query,
        ("123", 99900, product["scraped_at"])
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
    """Tests that each individual required key being absent raises a ValueError."""
    mock_connection = Mock()

    required_keys = ("product_id", "current_price", "scraped_at")

    # Test each missing key individually
    for missing_key in required_keys:
        product = {
            "product_id": "123",
            "current_price": 99900,
            "scraped_at": datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(0)))
        }
        del product[missing_key]

        with pytest.raises(ValueError, match="missing required keys"):
            insert_product_into_db(product, mock_connection)


def test_mark_products_defunct_valid():
    """Tests that mark_products_defunct executes the correct UPDATE query."""
    mock_connection = Mock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
    mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)

    urls = ["https://www.example.com/product/1", "https://www.example.com/product/2"]
    mark_products_defunct(urls, mock_connection)

    mock_cursor.execute.assert_called_once_with(
        "UPDATE products SET page_exists = FALSE WHERE product_url = ANY(%s)",
        (urls,)
    )
    mock_connection.commit.assert_called_once()


def test_mark_products_defunct_database_error_rolls_back():
    """Tests that a database error during mark_products_defunct triggers a rollback."""
    mock_connection = Mock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
    mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
    mock_cursor.execute.side_effect = psycopg2.DatabaseError("Connection failed")

    urls = ["https://www.example.com/product/1"]
    with pytest.raises(psycopg2.DatabaseError):
        mark_products_defunct(urls, mock_connection)

    mock_connection.rollback.assert_called_once()
    mock_connection.commit.assert_not_called()


def test_lambda_handler_inserts_valid_and_collects_defunct():
    """Tests that lambda_handler inserts valid products and collects defunct ones."""
    valid_product = {
        "product_id": "1",
        "url": "https://www.example.com/product/1",
        "current_price": "$999.00",
        "currency_code": "USD",
        "scraped_at": "2024-06-01T12:00:00Z",
        "page_exists": True,
    }
    defunct_product = {
        "product_id": "2",
        "url": "https://www.example.com/product/2",
        "current_price": "$0.00",
        "currency_code": "USD",
        "scraped_at": "2024-06-01T12:00:00Z",
        "page_exists": False,
    }

    mock_connection = Mock()
    with patch("lambda_handler.psycopg2.connect", return_value=mock_connection), \
         patch("lambda_handler.get_db_credentials", return_value={
             "host": "localhost", "port": 5432, "username": "user",
             "password": "pass", "dbname": "db"
         }), \
         patch("lambda_handler.insert_product_into_db") as mock_insert, \
         patch("lambda_handler.mark_products_defunct") as mock_defunct:

        result = lambda_handler([valid_product, defunct_product], None)

    assert result["inserted"] == 1
    assert len(result["defunct_products"]) == 1
    assert result["defunct_products"][0]["product_id"] == "2"
    mock_insert.assert_called_once()
    mock_defunct.assert_called_once_with(
        ["https://www.example.com/product/2"], mock_connection
    )
    mock_connection.close.assert_called_once()


def test_lambda_handler_skips_invalid_products():
    """Tests that lambda_handler skips products that fail cleaning (return None)."""
    invalid_product = {
        "product_name": "iPhone",
        # Missing all critical fields
    }

    mock_connection = Mock()
    with patch("lambda_handler.psycopg2.connect", return_value=mock_connection), \
         patch("lambda_handler.get_db_credentials", return_value={
             "host": "localhost", "port": 5432, "username": "user",
             "password": "pass", "dbname": "db"
         }), \
         patch("lambda_handler.insert_product_into_db") as mock_insert, \
         patch("lambda_handler.mark_products_defunct") as mock_defunct:

        result = lambda_handler([invalid_product], None)

    assert result["inserted"] == 0
    assert result["defunct_products"] == []
    mock_insert.assert_not_called()
    mock_defunct.assert_not_called()
    mock_connection.close.assert_called_once()
