# pylint: disable = redefined-outer-name
"""A script to scrape price and product data from the HTML content on a website."""

import logging
from datetime import datetime

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    import requests as curl_requests

from requests.exceptions import RequestException
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

log = logging.getLogger(__name__)

# Standard browser User-Agent for requests
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_html_content(url: str) -> str:
    """Fetches the HTML content for a given product."""
    if not isinstance(url, str):
        raise TypeError("URL must be a string.")

    try:
        if HAS_CURL_CFFI:
            response = curl_requests.get(url, impersonate="chrome", timeout=10)
        else:
            response = curl_requests.get(
                url, headers=BROWSER_HEADERS, timeout=10)
        if response.status_code == 404:
            log.warning("Page not found (404 Error): %s", url)
            return None
        response.raise_for_status()
        log.debug("Successfully fetched HTML content from URL: %s", url)
        return response.text

    except RequestException as e:
        log.error("Failed to fetch HTML content from URL: %s - %s", url, e)
        raise


def parse_html_content(content: str) -> BeautifulSoup:
    """Parses the HTML content for that product."""
    soup = BeautifulSoup(content, 'html.parser')
    log.debug("Parsed HTML content successfully.")
    return soup


def extract_current_price(soup: BeautifulSoup) -> str:
    """Extracts the current price of the product from the parsed HTML."""
    price = soup.find("span", attrs={"data-qa": "price-current"})
    if price:
        log.debug("Extracted current price successfully: %s",
                  price.text.strip())
        return price.text.strip()

    log.warning("Current price not found.")
    return None


def extract_currency_code(soup: BeautifulSoup) -> str:
    """Extracts the currency code of the product from the parsed HTML."""
    currency_meta = soup.find('meta', property='product:price:currency')
    if currency_meta:
        currency = currency_meta.get('content')
        log.debug("Extracted currency code successfully: %s", currency)
        return currency.strip()

    log.warning("Currency code not found in HTML.")
    return None


def extract_all_product_info(url: str, product_id: int, soup: BeautifulSoup) -> dict:
    """Extracts and returns relevant data for each product as a dictionary."""
    return {
        "product_id": product_id,
        "url": url,
        "current_price": extract_current_price(soup),
        "currency_code": extract_currency_code(soup),
        "page_exists": True,
        "scraped_at": datetime.now().isoformat()
    }


def create_product_info_not_found(url: str, product_id: int) -> dict:
    """Creates product dictionary when page doesn't exist (404)."""
    return {
        "product_id": product_id,
        "url": url,
        "current_price": None,
        "currency_code": None,
        "page_exists": False,
        "scraped_at": None
    }


def scrape_all_products(urls_and_ids: list[tuple]) -> list[dict]:
    """Scrapes information on all products from a given list of URLs and IDs."""
    if not isinstance(urls_and_ids, list):
        raise TypeError(
            "Must pass a list of tuples containing product URLs and IDs.")

    log.info("Starting to scrape %d products", len(urls_and_ids))
    products = []

    for url, product_id in urls_and_ids:
        try:
            response = fetch_html_content(url)
            if response is None:  # Page doesn't exist anymore (404)
                product_info = create_product_info_not_found(url, product_id)
            else:
                soup = parse_html_content(response)
                product_info = extract_all_product_info(url, product_id, soup)
            products.append(product_info)
            log.info("Successfully scraped product information from URL: %s", url)
        except Exception as e:
            log.error("Failed to scrape URL: %s - %s", url, e)

    return products


if __name__ == "__main__":
    # Example usage
    urls_and_ids = [
        ("https://www.overclockers.co.uk/medion-erazer-crawler-e30e-nvidia-rtx-2050-16gb-15.6-fhd-intel-i5-13420h-ga-lap-mdn-05630.html", 1)
    ]

    scraped_products = scrape_all_products(urls_and_ids)
    for product in scraped_products:
        print(product)
