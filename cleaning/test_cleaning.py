"""Tests for the cleaning script."""
from datetime import datetime, timezone, timedelta
import pytest
from cleaning import (
    clean_product_name,
    parse_price,
    clean_currency,
    convert_to_datetime,
    valid_url,
    clean_product_data
)


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
    assert parse_price("$999.00") == 99900
    assert parse_price("£899.00") == 89900
    assert parse_price("€799.00") == 79900
    assert parse_price("699.00 €") == 69900


def test_parse_price_invalid_format_raises_error():
    """Tests that an invalid price format raises a ValueError."""
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


def test_parse_price_integer_format():
    """Tests parse_price with integer-only amounts (no decimal places).

    Even without decimal places, values are treated as major currency units
    and multiplied by 100 for consistency.
    """
    assert parse_price("₹1000") == 100000
    assert parse_price("¥5000") == 500000
    assert parse_price("₹99999") == 9999900


def test_parse_price_with_commas():
    """Tests parse_price with comma-separated thousands."""
    assert parse_price("$1,000.00") == 100000
    assert parse_price("£10,500.50") == 1050050
    assert parse_price("€1,234,567.89") == 123456789


def test_parse_price_single_decimal_place():
    """Tests parse_price with single decimal place."""
    assert parse_price("$99.9") == 9990
    assert parse_price("£1.5") == 150


def test_parse_price_zero_decimal():
    """Tests parse_price with .00 decimal."""
    assert parse_price("$0.00") == 0
    assert parse_price("£10.00") == 1000


def test_parse_price_whitespace_handling():
    """Tests parse_price with extra whitespace."""
    assert parse_price("  $999.00  ") == 99900
    assert parse_price("  £  899.00  ") == 89900
    assert parse_price("699.00   €") == 69900


def test_parse_price_empty_string_raises_error():
    """Tests that an empty price string raises a ValueError."""
    with pytest.raises(ValueError):
        parse_price("")
    with pytest.raises(ValueError):
        parse_price("   ")


def test_clean_currency_valid():
    """Tests the clean_currency function."""
    assert clean_currency("USD") == "USD"
    assert clean_currency("usd") == "USD"
    assert clean_currency(" UsD ") == "USD"


def test_clean_currency_invalid_raises_error():
    """Tests that an invalid currency code raises a ValueError."""
    with pytest.raises(ValueError):
        clean_currency("U")
    with pytest.raises(ValueError):
        clean_currency("US")
    with pytest.raises(ValueError):
        clean_currency("USDA")


def test_clean_currency_non_string_raises_error():
    """Tests that a non-string currency raises a TypeError."""
    with pytest.raises(TypeError):
        clean_currency(123)
    with pytest.raises(TypeError):
        clean_currency(None)


def test_valid_url():
    """Tests the valid_url function."""
    assert valid_url("https://www.example.com/product/123") is True
    assert valid_url("https://www.example.com/product/123/sdaf/456") is True
    assert valid_url("http://www.example.com/product/123") is True
    assert valid_url("www.example.com/product/123") is True
    assert valid_url("example.com/product/123") is False
    assert valid_url("") is False


def test_valid_url_non_string_raises_error():
    """Tests that a non-string URL raises a TypeError."""
    with pytest.raises(TypeError):
        valid_url(123)
    with pytest.raises(TypeError):
        valid_url(None)


def test_convert_to_datetime():
    """Tests the convert_to_datetime function."""
    assert convert_to_datetime(
        "2024-06-01T12:00:00Z") == datetime(
            2024, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(0))
    )
    assert convert_to_datetime(
        "2024-06-01T12:00:00+00:00") == datetime(
            2024, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(0))
    )
    assert convert_to_datetime(
        "2024-06-01T12:00:00-00:00") == datetime(
            2024, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(0))
    )


def test_convert_to_datetime_invalid_format_raises_error():
    """Tests that an invalid datetime format raises a ValueError."""
    with pytest.raises(ValueError):
        convert_to_datetime("2024/06/01T12:00:00Z")
    with pytest.raises(ValueError):
        convert_to_datetime("June 1, 2024 12:00:00")


def test_convert_to_datetime_non_string_raises_error():
    """Tests that a non-string datetime raises a TypeError."""
    with pytest.raises(TypeError):
        convert_to_datetime(123)
    with pytest.raises(TypeError):
        convert_to_datetime(None)


def test_clean_product_data():
    """Tests the clean_product_data function."""
    product = {
        "product_name": "  Apple iPhone 13  ",
        "original_price": "$1099.00",
        "current_price": "$999.00",
        "currency_code": "usd",
        "url": "https://www.example.com/product/123",
        "website_name": "ExampleStore",
        "scraped_at": "2024-06-01T12:00:00Z",
        "product_id": "123",
        "page_exists": True
    }
    result = clean_product_data(product)
    assert result["current_price"] == 99900
    assert result["currency_code"] == "USD"
    assert result["scraped_at"] == datetime(
        2024, 6, 1, 12, 0, 0, tzinfo=timezone(timedelta(0)))


def test_clean_product_data_non_dict_raises_error():
    """Tests that non-dict input raises a TypeError."""
    with pytest.raises(TypeError):
        clean_product_data("not a dict")
    with pytest.raises(TypeError):
        clean_product_data(None)


def test_clean_product_data_missing_critical_keys_returns_none():
    """Tests that products with missing critical keys return None (are skipped)."""
    incomplete_product = {
        "product_name": "iPhone",
        "original_price": "$1099.00",
    }
    result = clean_product_data(incomplete_product)
    assert result is None
