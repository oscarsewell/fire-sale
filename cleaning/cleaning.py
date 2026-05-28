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
import regex

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clean_product_name(product_name: str) -> str:
    """Cleans the product name by removing leading and trailing whitespace."""
    logger.debug("Cleaning product name: '%s'", product_name)

    if not isinstance(product_name, str):
        logger.error("Product name is not a string: %r", product_name)
        raise TypeError("Product name must be a string.")

    if not product_name.strip():
        logger.error("Product name is empty or whitespace.")
        raise ValueError("Product name cannot be empty or whitespace.")

    if len(product_name) > 255:
        logger.error(
            "Product name exceeds 255 characters (length=%d).", len(product_name))
        raise ValueError("Product name cannot exceed 255 characters.")

    cleaned = product_name.strip()
    logger.info("Product name cleaned: '%s'", cleaned)
    return cleaned


def parse_price(price_str: str) -> tuple:
    """Parses a price string and returns the currency symbol and the numeric price."""
    logger.debug("Parsing price string: '%s'", price_str)

    if not isinstance(price_str, str):
        logger.error("Price is not a string: %r", price_str)
        raise TypeError("Price must be a string.")

    price_str = price_str.strip()

    if not price_str:
        logger.error("Price string is empty.")
        raise ValueError("Price cannot be empty.")

    # Match either "<currency><amount>" or "<amount><currency>" using Unicode currency class.
    match = regex.match(
        r'^\s*(?:(?P<leading>\p{Sc})\s*)?'
        r'(?P<amount>[\d,]+(?:\.\d{1,2})?)'
        r'(?:\s*(?P<trailing>\p{Sc}))?\s*$',
        price_str,
    )

    if not match:
        logger.error(
            "Price string did not match expected format: '%s'", price_str)
        raise ValueError(f"Invalid price format: {price_str}")

    leading_symbol = match.group("leading")
    trailing_symbol = match.group("trailing")

    if not leading_symbol and not trailing_symbol:
        logger.error("No currency symbol found in price: '%s'", price_str)
        raise ValueError(f"Invalid price format: {price_str}")

    if leading_symbol and trailing_symbol and leading_symbol != trailing_symbol:
        logger.error("Conflicting currency symbols '%s' and '%s' in: '%s'",
                     leading_symbol, trailing_symbol, price_str)
        raise ValueError(f"Conflicting currency symbols in: {price_str}")

    currency_symbol = leading_symbol or trailing_symbol
    numeric_price = match.group("amount").replace(',', '')

    try:
        price = float(numeric_price)
    except ValueError as e:
        logger.error("Could not convert amount to float: '%s'", numeric_price)
        raise ValueError(f"Invalid numeric price: {numeric_price}") from e

    logger.info("Parsed price: %s %.2f", currency_symbol, price)
    return currency_symbol, price


def normalize_product_prices(product: dict) -> dict:
    """Normalizes the original_price and current_price fields in the product dictionary,
    adding a currency field."""
    logger.debug("Normalizing product prices.")

    if not isinstance(product, dict):
        logger.error("Product is not a dictionary: %r", product)
        raise TypeError("Product must be a dictionary.")

    if "original_price" not in product or "current_price" not in product:
        logger.error("Product is missing 'original_price' or 'current_price'.")
        raise ValueError(
            "Product must contain 'original_price' and 'current_price' fields.")

    original_currency_symbol, original_price = parse_price(
        product["original_price"])
    current_currency_symbol, current_price = parse_price(
        product["current_price"])

    if not original_currency_symbol or not current_currency_symbol:
        logger.error("One or both prices are missing a currency symbol.")
        raise ValueError("Both prices must contain a valid currency symbol.")

    if original_currency_symbol != current_currency_symbol:
        logger.error(
            "Currency mismatch: original='%s', current='%s'",
            original_currency_symbol, current_currency_symbol
        )
        raise ValueError("Currency symbols do not match.")

    product["original_price"] = original_price
    product["current_price"] = current_price
    product["currency"] = original_currency_symbol

    logger.info(
        "Prices normalized: original=%.2f, current=%.2f, currency='%s'",
        original_price, current_price, original_currency_symbol
    )
    return product


def calculate_discount_percentage(original_price: float, current_price: float) -> float:
    """Calculates the discount percentage."""
    if not isinstance(original_price, (int, float)) or not isinstance(current_price, (int, float)):
        logger.error("Non-numeric prices provided: original=%r, current=%r",
                     original_price, current_price)
        raise TypeError("Prices must be numeric.")

    logger.debug("Calculating discount: original=%.2f, current=%.2f",
                 original_price, current_price)

    if original_price <= 0:
        logger.error("Original price is not positive: %.2f", original_price)
        raise ValueError("Original price must be greater than zero.")

    if current_price < 0:
        logger.error("Current price is negative: %.2f", current_price)
        raise ValueError("Current price cannot be negative.")

    discount_percentage = (
        (original_price - current_price) / original_price
    ) * 100
    result = round(discount_percentage, 2)
    logger.info("Discount calculated: %.2f%%", result)
    return result


def convert_to_datetime(scraped_at: str) -> datetime:
    """Converts the scraped_at string to a datetime object."""
    logger.debug("Converting timestamp: '%s'", scraped_at)

    if not isinstance(scraped_at, str):
        logger.error("scraped_at is not a string: %r", scraped_at)
        raise TypeError("scraped_at must be a string.")

    try:
        dt = datetime.fromisoformat(scraped_at.replace("Z", "+00:00"))
        logger.info("Timestamp converted: %s", dt)
        return dt
    except ValueError as e:
        logger.error("Failed to parse timestamp: '%s'", scraped_at)
        raise ValueError(f"Invalid datetime format: {scraped_at}") from e


def valid_url(product_url: str) -> bool:
    """Tests if the product URL is valid."""
    logger.debug("Validating URL: '%s'", product_url)

    if not isinstance(product_url, str):
        logger.error("URL is not a string: %r", product_url)
        raise TypeError("URL must be a string.")

    url_pattern = re.compile(
        r'^(https?://)?'  # optional http or https scheme
        r'(www\.)'
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # domain name
        r'(/[\w\-./?%&=]*)?$'  # optional path and query string
    )
    is_valid = bool(url_pattern.match(product_url))
    if is_valid:
        logger.info("URL is valid: '%s'", product_url)
    else:
        logger.warning("URL is invalid: '%s'", product_url)
    return is_valid


def clean_product_data(product: dict) -> dict:
    """Cleans and normalizes the product data."""
    logger.info("Starting full product data clean.")

    if not isinstance(product, dict):
        logger.error("product is not a dictionary: %r", product)
        raise TypeError("product must be a dictionary.")

    required_keys = ("scraped_at",)
    missing_keys = [key for key in required_keys if key not in product]
    if missing_keys:
        logger.error("product is missing required keys: %s", missing_keys)
        raise ValueError(
            f"product is missing required keys: {', '.join(missing_keys)}"
        )

    product["product_name"] = clean_product_name(
        product.get("product_name", ""))
    product = normalize_product_prices(product)
    product["scraped_at"] = convert_to_datetime(product["scraped_at"])
    logger.info("Product data clean complete.")
    return product


if __name__ == "__main__":
    example_product = {
        "product_name": "  Apple iPhone 13 Pro Max  ",
        "original_price": "$1099.00",
        "current_price": "$999.00",
        "url": "https://www.example.com/product/iphone-13-pro-max",
        "website_name": "ExampleStore",
        "scraped_at": "2024-06-01T12:00:00Z"
    }
    example_product = clean_product_data(example_product)
    print(example_product)
