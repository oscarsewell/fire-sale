"""This module provides functions to clean and process scraped product data. 
It includes functions to clean product names, extract currency symbols, 
convert price strings to floats, calculate discount percentages, 
and convert timestamp strings to datetime objects."""

import logging
from datetime import datetime
import re
import regex
import iso4217

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


def parse_price(price_str: str) -> int:
    """Parses a price string and returns the numeric price as an int.

    Always interprets the input as a major currency unit and converts to 
    the smallest unit (multiply by 100). For example:
    - "$10.00" → 1000 (10 dollars = 1000 cents)
    - "$10" → 1000 (10 dollars = 1000 cents)  
    - "₹1000" → 100000 (1000 rupees = 100000 paise)

    This ensures consistent behavior regardless of whether the input
    includes decimal places.
    """
    logger.debug("Parsing price string: '%s'", price_str)

    if not isinstance(price_str, str):
        logger.error("Price is not a string: %r", price_str)
        raise TypeError("Price must be a string.")

    price_str = price_str.strip()

    if not price_str:
        logger.error("Price string is empty.")
        raise ValueError("Price cannot be empty.")

    # Match numeric amount, optionally with currency symbol
    match = regex.match(
        r'^\s*(?:\p{Sc}\s*)?'
        r'(?P<amount>[\d,]+(?:\.\d{1,2})?)'
        r'(?:\s*\p{Sc})?\s*$',
        price_str,
    )

    if not match:
        logger.error(
            "Price string did not match expected format: '%s'", price_str)
        raise ValueError(f"Invalid price format: {price_str}")

    numeric_price = match.group("amount").replace(',', '')

    try:
        price_float = float(numeric_price)
        # Always convert to smallest currency unit (multiply by 100)
        price_result = int(round(price_float * 100))
        logger.info("Parsed price: amount=%.2f (converted to smallest unit=%d)",
                    price_float, price_result)
        return price_result

    except ValueError as e:
        logger.error(
            "Failed to convert price amount to float: '%s'", numeric_price)
        raise ValueError(f"Invalid numeric price: {numeric_price}") from e


def clean_currency(currency: str) -> str:
    """Cleans the currency string by stripping whitespace and validating it
    against ISO 4217 currency codes."""
    logger.debug("Cleaning currency: '%s'", currency)

    if not isinstance(currency, str):
        logger.error("Currency is not a string: %r", currency)
        raise TypeError("Currency must be a string.")

    cleaned_currency = currency.strip().upper()

    try:
        iso4217.Currency(cleaned_currency)
    except (KeyError, ValueError):
        logger.error("Invalid currency code: '%s'", cleaned_currency)
        raise ValueError(f"Invalid currency code: {cleaned_currency}")

    logger.info("Currency cleaned: '%s'", cleaned_currency)
    return cleaned_currency


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


def check_page_exists_bool(page_exists) -> bool:
    """Checks if the page_exists value is a boolean."""
    logger.debug("Checking page_exists value: %r", page_exists)

    if isinstance(page_exists, bool):
        logger.info("page_exists is a valid boolean: %r", page_exists)
        return page_exists
    else:
        logger.error("page_exists is not a boolean: %r", page_exists)
        raise TypeError("page_exists must be a boolean.")


def clean_product_data(product: dict) -> dict:
    """Cleans and normalizes the product data."""
    logger.info("Starting full product data clean.")

    if not isinstance(product, dict):
        logger.error("product is not a dictionary: %r", product)
        raise TypeError("product must be a dictionary.")

    required_keys = (
        "product_id",
        "url",
        "current_price",
        "currency_code",
        "scraped_at",
        "page_exists"
    )
    missing_keys = [key for key in required_keys if key not in product]
    if missing_keys:
        logger.error("product is missing required keys: %s", missing_keys)
        raise ValueError(
            f"product is missing required keys: {', '.join(missing_keys)}"
        )

    try:
        if product.get("product_name") is not None:
            product["product_name"] = clean_product_name(
                product.get("product_name", "")
            )
        else:
            return None
        if product.get("original_price") is not None:
            product["original_price"] = parse_price(
                product["original_price"]
            )
        else:
            return None
        if product.get("current_price") is not None:
            product["current_price"] = parse_price(
                product["current_price"]
            )
        else:
            return None
        if product.get("currency_code") is not None:
            product["currency_code"] = clean_currency(
                product["currency_code"]
            )
        else:
            return None
        if product.get("scraped_at") is not None:
            product["scraped_at"] = convert_to_datetime(
                product["scraped_at"]
            )
        else:
            return None
        if product.get("url") is not None:
            if valid_url(product["url"]):
                product["url"] = product["url"].strip()
            else:
                logger.warning("URL is invalid, skipping product")
                raise ValueError(f"Invalid URL: {product['url']}")
        if product.get("page_exists") is not None:
            product["page_exists"] = check_page_exists_bool(
                product["page_exists"]
            )
            if product.get("page_exists") is False:
                logger.warning("Page does not exist, skipping product")

        logger.info("Product data clean complete.")
        return product
    except Exception as e:
        logger.error("Error during product data cleaning: %s", str(e))
        raise


if __name__ == "__main__":
    example_product = {
        "product_id": 67,
        "product_name": "  Apple iPhone 13 Pro Max  ",
        "original_price": "$1099.00",
        "current_price": "$999.00",
        "currency_code": "USD",
        "url": "https://www.example.com/product/iphone-13-pro-max",
        "website_name": "ExampleStore",
        "scraped_at": "2024-06-01T12:00:00Z"
    }
    print(clean_product_data(example_product))
