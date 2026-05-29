"""Tests for the cleaning script."""
from datetime import datetime, timezone, timedelta
from cleaning import clean_product_data
import pytest
from cleaning import (
    clean_product_name,
    parse_price,
    clean_currency,
    calculate_discount_percentage,
    convert_to_datetime,
    valid_url,
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


def test_calculate_discount_percentage():
    """Tests the calculate_discount_percentage function."""
    assert calculate_discount_percentage(1099.00, 999.00) == 9.10
    assert calculate_discount_percentage(899.00, 799.00) == 11.12
    assert calculate_discount_percentage(799.00, 699.00) == 12.52


def test_calculate_discount_percentage_invalid_type_raises_error():
    """Tests that non-numeric prices raise a TypeError."""
    with pytest.raises(TypeError):
        calculate_discount_percentage("999.00", 899.00)
    with pytest.raises(TypeError):
        calculate_discount_percentage(999.00, "899.00")
    with pytest.raises(TypeError):
        calculate_discount_percentage(None, 899.00)
    with pytest.raises(TypeError):
        calculate_discount_percentage(999.00, None)


def test_calculate_discount_percentage_invalid_value_raises_error():
    """Tests that invalid price values raise a ValueError."""
    with pytest.raises(ValueError):
        calculate_discount_percentage(0, 899.00)
    with pytest.raises(ValueError):
        calculate_discount_percentage(-999.00, 899.00)
    with pytest.raises(ValueError):
        calculate_discount_percentage(999.00, -899.00)


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
