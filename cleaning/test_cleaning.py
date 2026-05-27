"""Tests for the cleaning script."""
from cleaning import (
    clean_product_name,
    parse_price,
    normalize_product_prices,
    calculate_discount_percentage,
    convert_to_datetime,
    valid_url,
    valid_discount_percentage,
)
from datetime import datetime
import pytest


def test_clean_product_name():
    """Tests the clean_product_name function."""
    assert clean_product_name(
        "  Apple iPhone 13 Pro Max  ") == "Apple iPhone 13 Pro Max"


def test_clean_product_name_empty_raises_error():
    """Tests that an empty product name raises a ValueError."""
    with pytest.raises(ValueError):
        clean_product_name("   ")


def test_clean_product_name_non_string_raises_error():
    """Tests that a non-string product name raises a TypeError."""
    with pytest.raises(TypeError):
        clean_product_name(123)


def test_clean_product_name_none_raises_error():
    """Tests that a None product name raises a TypeError."""
    with pytest.raises(TypeError):
        clean_product_name(None)


def test_clean_product_name_over_max_length_raises_error():
    """Tests that a product name over the maximum length raises a ValueError."""
    with pytest.raises(ValueError):
        clean_product_name("A" * 256)


def test_parse_price():
    """Tests the parse_price function."""
    assert parse_price("$999.00") == ("$", 999.00)
    assert parse_price("£899.00") == ("£", 899.00)
    assert parse_price("€799.00") == ("€", 799.00)
    assert parse_price("699.00 €") == ("€", 699.00)


def test_parse_price_invalid_format_raises_error():
    """Tests that an invalid price format raises a ValueError."""
    with pytest.raises(ValueError):
        parse_price("999.00")
    with pytest.raises(ValueError):
        parse_price("$999.00 USD")
    with pytest.raises(ValueError):
        parse_price("USD 999.00")


def test_parse_price_non_string_raises_error():
    """Tests that a non-string price raises a TypeError."""
    with pytest.raises(TypeError):
        parse_price(999.00)
    with pytest.raises(TypeError):
        parse_price(None)


def test_normalize_product_prices():
    """Tests the normalize_product_prices function."""
    product = {
        "product_name": "Apple iPhone 13 Pro Max",
        "original_price": "$999.00",
        "current_price": "$899.00",
        "url": "https://www.example.com/product/123",
        "website_name": "EBuyer",
        "scraped_at": "2024-06-01T12:00:00Z"
    }
    normalized_product = normalize_product_prices(product)
    assert normalized_product["original_price"] == 999.00
    assert normalized_product["current_price"] == 899.00
    assert normalized_product["currency"] == "$"


def test_normalize_product_prices_wrong_type_raises_error():
    """Tests that a non-dictionary product raises a TypeError."""
    with pytest.raises(TypeError):
        normalize_product_prices("not a dictionary")
    with pytest.raises(TypeError):
        normalize_product_prices(None)


def test_normalize_product_prices_invalid_price_raises_error():
    """Tests that an invalid price format raises a ValueError."""
    product = {
        "product_name": "Apple iPhone 13 Pro Max",
        "original_price": "999.00",
        "current_price": "$899.00",
        "url": "https://www.example.com/product/123",
        "website_name": "EBuyer",
        "scraped_at": "2024-06-01T12:00:00Z"
    }
    with pytest.raises(ValueError):
        normalize_product_prices(product)


def test_normalize_product_prices_non_string_price_raises_error():
    """Tests that a non-string price raises a TypeError."""
    product = {
        "product_name": "Apple iPhone 13 Pro Max",
        "original_price": 999.00,
        "current_price": "$899.00",
        "url": "https://www.example.com/product/123",
        "website_name": "EBuyer",
        "scraped_at": "2024-06-01T12:00:00Z"
    }
    with pytest.raises(TypeError):
        normalize_product_prices(product)


def test_normalize_product_prices_missing_price_raises_error():
    """Tests that a missing price raises a ValueError."""
    product = {
        "product_name": "Apple iPhone 13 Pro Max",
        "url": "https://www.example.com/product/123",
        "website_name": "EBuyer",
        "scraped_at": "2024-06-01T12:00:00Z"
    }
    with pytest.raises(ValueError):
        normalize_product_prices(product)


def test_normalize_product_prices_invalid_currency_raises_error():
    """Tests that an invalid currency symbol raises a ValueError."""
    product = {
        "product_name": "Apple iPhone 13 Pro Max",
        "original_price": "999.00",
        "current_price": "899.00",
        "url": "https://www.example.com/product/123",
        "website_name": "EBuyer",
        "scraped_at": "2024-06-01T12:00:00Z"
    }
    with pytest.raises(ValueError):
        normalize_product_prices(product)


def test_normalize_product_prices_different_currencies_raises_error():
    """Tests that different currency symbols in original_price and current_price raise a ValueError."""
    product = {
        "product_name": "Apple iPhone 13 Pro Max",
        "original_price": "$999.00",
        "current_price": "£899.00",
        "url": "https://www.example.com/product/123",
        "website_name": "EBuyer",
        "scraped_at": "2024-06-01T12:00:00Z"
    }
    with pytest.raises(ValueError):
        normalize_product_prices(product)


def test_valid_url():
    """Tests the valid_url function."""
    assert valid_url("https://www.example.com/product/123") is True
    assert valid_url("http://www.example.com/product/123") is True
    assert valid_url("www.example.com/product/123") is False
    assert valid_url("example.com/product/123") is False
    assert valid_url("") is False
    assert valid_url(None) is False


def test_valid_discount_percentage():
    """Tests the valid_discount_percentage function."""
    assert valid_discount_percentage(0) is True
    assert valid_discount_percentage(50) is True
    assert valid_discount_percentage(67.74) is True
    assert valid_discount_percentage(100) is True
    assert valid_discount_percentage(-1) is False
    assert valid_discount_percentage(101) is False


def test_calculate_discount_percentage():
    """Tests the calculate_discount_percentage function."""
    assert calculate_discount_percentage(1099.00, 999.00) == 9.10
    assert calculate_discount_percentage(899.00, 799.00) == 11.12
    assert calculate_discount_percentage(799.00, 699.00) == 12.52


def test_convert_to_datetime():
    """Tests the convert_to_datetime function."""
    assert convert_to_datetime(
        "2024-06-01T12:00:00Z") == datetime(2024, 6, 1, 12, 0, 0)
    assert convert_to_datetime(
        "2024-06-01T12:00:00+00:00") == datetime(2024, 6, 1, 12, 0, 0)
    assert convert_to_datetime(
        "2024-06-01T12:00:00-00:00") == datetime(2024, 6, 1, 12, 0, 0)


def test_convert_to_datetime_invalid_format_raises_error():
    """Tests that an invalid datetime format raises a ValueError."""
    with pytest.raises(ValueError):
        convert_to_datetime("2024-06-01 12:00:00")
    with pytest.raises(ValueError):
        convert_to_datetime("2024/06/01T12:00:00Z")
    with pytest.raises(ValueError):
        convert_to_datetime("June 1, 2024 12:00:00")
