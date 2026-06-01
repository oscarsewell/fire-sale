"""Tests for the tracked product checker lambda."""
import pytest
import psycopg2
from unittest.mock import Mock, patch
from tracked_product_checker import (
    get_base_url,
    get_db_credentials,
    get_tracked_products_by_site
)


def test_get_base_url():
    """Test that get_base_url correctly extracts the base URL from a product URL."""
    url = "https://www.example.com/product/12345?ref=abc"
    expected_base_url = "www.example.com"
    assert get_base_url(url) == expected_base_url


def test_get_base_url_no_scheme():
    """Test that get_base_url correctly handles URLs without a scheme."""
    url = "www.example.com/product/12345?ref=abc"
    expected_base_url = "www.example.com"
    assert get_base_url(url) == expected_base_url


def test_get_base_url_with_subdomain():
    """Test that get_base_url correctly handles URLs with subdomains."""
    url = "https://subdomain.example.com/product/12345?ref=abc"
    expected_base_url = "subdomain.example.com"
    assert get_base_url(url) == expected_base_url


def test_get_base_url_raises_on_invalid_url():
    """Test that get_base_url raises an exception for invalid URLs."""
    url = "not a valid url"
    with pytest.raises(ValueError):
        get_base_url(url)


def test_get_base_url_raises_on_url_with_spaces():
    """Test that get_base_url raises an exception for URLs with spaces."""
    url = "https://www.example.com/product with spaces/12345"
    with pytest.raises(ValueError, match="contains spaces"):
        get_base_url(url)


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
    monkeypatch.delenv("DB_SECRET_ARN", raising=False)

    with pytest.raises(ValueError):
        get_db_credentials()


def test_get_tracked_products_by_site(monkeypatch):
    """Test that get_tracked_products_by_site correctly groups products by site."""
    # Mock database cursor with fake data
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [
        (1, "https://www.ebuyer.com/product/1", "ebuyer"),
        (2, "https://www.ebuyer.com/product/2", "ebuyer"),
        (3, "https://www.overclockers.co.uk/product/1", "overclockers"),
        (4, "https://www.unknown-site.com/product/1", None),  # site_name is NULL
    ]
    # Make cursor support context manager protocol
    mock_cursor.__enter__ = Mock(return_value=mock_cursor)
    mock_cursor.__exit__ = Mock(return_value=None)

    # Mock database connection
    mock_connection = Mock()
    mock_connection.cursor.return_value = mock_cursor

    # Patch psycopg2.connect and get_db_credentials
    with patch("psycopg2.connect", return_value=mock_connection):
        products_by_site = get_tracked_products_by_site()

    # Assert grouping is correct
    assert isinstance(products_by_site, dict)
    assert "ebuyer" in products_by_site
    assert "overclockers" in products_by_site
    assert "www.unknown-site.com" in products_by_site  # base URL for NULL site

    # Assert correct number of products per site
    assert len(products_by_site["ebuyer"]) == 2
    assert len(products_by_site["overclockers"]) == 1
    assert len(products_by_site["www.unknown-site.com"]) == 1

    # Assert products are lists
    assert products_by_site["ebuyer"] == [
        [1, "https://www.ebuyer.com/product/1"], [2, "https://www.ebuyer.com/product/2"]]
    assert products_by_site["overclockers"] == [
        [3, "https://www.overclockers.co.uk/product/1"]]
    assert products_by_site["www.unknown-site.com"] == [[4,
                                                         "https://www.unknown-site.com/product/1"]]


def test_get_tracked_products_by_site_database_error():
    """Test that get_tracked_products_by_site handles database errors gracefully."""

    # Mock database connection that raises an error
    mock_connection = Mock()
    mock_connection.cursor.side_effect = psycopg2.DatabaseError(
        "Connection failed")

    with patch("psycopg2.connect", return_value=mock_connection):
        with pytest.raises(psycopg2.DatabaseError):
            get_tracked_products_by_site()
