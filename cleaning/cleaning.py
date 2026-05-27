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


def clean_product_name(product_name: str) -> str:
    """Cleans the product name by removing leading and trailing whitespace."""
    if not isinstance(product_name, str):
        raise TypeError("Product name must be a string.")
    
    if not product_name.strip():
        raise ValueError("Product name cannot be empty or whitespace.")
    
    if len(product_name) > 255:
        raise ValueError("Product name cannot exceed 255 characters.")
    
    return product_name.strip()


def parse_price(price_str: str) -> tuple:
    """Parses a price string and returns the currency symbol and the numeric price."""
    

def normalize_product_prices(product: dict) -> dict:
    """Normalizes the original_price and current_price fields in the product dictionary,
    adding a currency field."""


def calculate_discount_percentage(original_price: float, current_price: float) -> float:
    """Calculates the discount percentage."""


def convert_to_datetime(scraped_at: str) -> int:
    """Converts the scraped_at string to a timestamp."""


def valid_url(product_url: str) -> bool:
    """Tests if the product URL is valid."""


def valid_discount_percentage(discount_percentage: float) -> bool:
    """Tests if the discount percentage is valid."""


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
