"""Tests for the tracked product checker lambda."""
import pytest
from tracked_product_checker import (
    get_base_url,
    get_db_credentials,
    get_tracked_products_by_site
)
import monkeypatch


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


def test_get_db_credentials():
    """Test that get_db_credentials returns a dictionary with the expected keys."""
    credentials = get_db_credentials()
    assert isinstance(credentials, dict)
    assert "host" in credentials
    assert "port" in credentials
    assert "username" in credentials
    assert "password" in credentials
    assert "dbname" in credentials


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


def test_get_tracked_products_by_site():
    """Test that get_tracked_products_by_site returns a dictionary."""
    products_by_site = get_tracked_products_by_site()
    assert isinstance(products_by_site, dict)
