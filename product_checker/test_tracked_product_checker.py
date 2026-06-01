"""Tests for the tracked product checker lambda."""
import pytest
import product_checker.tracked_product_checker as tracked_product_checker

get_base_url = tracked_product_checker.get_base_url
get_db_credentials = tracked_product_checker.get_db_credentials
get_tracked_products_by_site = tracked_product_checker.get_tracked_products_by_site

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


def test_get_tracked_products_by_site():
    """Test that get_tracked_products_by_site returns a dictionary."""
    products_by_site = get_tracked_products_by_site()
    assert isinstance(products_by_site, dict)
