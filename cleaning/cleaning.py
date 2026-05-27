"""This module provides functions to clean and process scraped product data. 
It includes functions to clean product names, extract currency symbols, 
convert price strings to floats, calculate discount percentages, 
and convert timestamp strings to datetime objects."""

# dictionary format:
# {
# "product_name": "",
# "original_price": "$999.00"
# "current_price": "$899.00",
# "url": "",
# "website_name": "EBuyer",
# "scraped_at": "[timestamp]"
# }
#

import logging
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_string(string: str) -> str:
    """Cleans the product name by removing leading and trailing whitespace."""
    return string.strip()


def get_currency_symbol(price: str) -> str:
    """Gets the currency symbol from the price string."""
    return price[0]  # Assuming the currency symbol is the first character


def clean_price(price: str) -> float:
    """Cleans the price by separating the currency symbol and converting it to a float"""
    return float(price[1:])


def calculate_discount_percentage(original_price: float, current_price: float) -> float:
    """Calculates the discount percentage."""


def convert_to_datetime(scraped_at: str) -> int:
    """Converts the scraped_at string to a timestamp."""


if __name__ == "__main__":
    example_product = {
        "product_name": "  Apple iPhone 13 Pro Max  ",
        "original_price": "$1099.00",
        "current_price": "$999.00",
        "url": "https://www.example.com/product/iphone-13-pro-max",
        "website_name": "ExampleStore",
        "scraped_at": "2024-06-01T12:00:00Z"
    }
    example_product["currency"] = get_currency_symbol(
        example_product["current_price"])
