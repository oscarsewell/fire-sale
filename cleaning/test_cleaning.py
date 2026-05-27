"""Tests for the cleaning script."""
from cleaning import (
    clean_string,
    get_currency_symbol,
    clean_price,
    calculate_discount_percentage,
    convert_to_datetime
)
from datetime import datetime


def test_clean_string():
    """Tests the clean_string function."""
    assert clean_string(
        "  Apple iPhone 13 Pro Max  ") == "Apple iPhone 13 Pro Max"


def test_get_currency_symbol():
    """Tests the get_currency_symbol function."""
    assert get_currency_symbol("$999.00") == "$"
    assert get_currency_symbol("£899.00") == "£"
    assert get_currency_symbol("799.00 €") == "€"
    assert get_currency_symbol("¥699.00") == "¥"


def test_clean_price():
    """Tests the clean_price function."""
    assert clean_price("$999.00") == 999.00
    assert clean_price("£899.00") == 899.00
    assert clean_price("799.00 €") == 799.00
    assert clean_price("¥699.00") == 699.00


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
