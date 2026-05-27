"""Tests for the cleaning script."""
from cleaning import (
    clean_product_name,
    get_currency_symbol,
    clean_price,
    calculate_discount_percentage,
    convert_to_datetime
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


def test_get_currency_symbol():
    """Tests the get_currency_symbol function."""
    assert get_currency_symbol("$999.00") == "$"
    assert get_currency_symbol("£899.00") == "£"
    assert get_currency_symbol("799.00 €") == "€"
    assert get_currency_symbol("¥699.00") == "¥"


def test_get_currency_symbol_empty_raises_error():
    """Tests that an empty price string raises a ValueError."""
    with pytest.raises(ValueError):
        get_currency_symbol("")


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
