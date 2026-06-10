# pylint: disable = redefined-outer-name
"""A script to scrape price and product data from the HTML content on a website."""

import logging
import os
import re
from datetime import datetime

try:
    from curl_cffi import requests
    HAS_CURL_CFFI = True
except ImportError:
    import requests
    HAS_CURL_CFFI = False

from requests.exceptions import RequestException
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

log = logging.getLogger(__name__)

# Bright Data ISP Proxy configuration from environment variables
BRIGHTDATA_HOST = os.environ.get("BRIGHTDATA_HOST", "")
BRIGHTDATA_PORT = os.environ.get("BRIGHTDATA_PORT", "")
BRIGHTDATA_USERNAME = os.environ.get("BRIGHTDATA_USERNAME", "")
BRIGHTDATA_PASSWORD = os.environ.get("BRIGHTDATA_PASSWORD", "")


def get_proxy_dict() -> dict:
    """Builds proxy configuration dictionary from environment variables."""
    if not all([BRIGHTDATA_HOST, BRIGHTDATA_PORT, BRIGHTDATA_USERNAME, BRIGHTDATA_PASSWORD]):
        log.warning("Proxy not configured - missing environment variables. Host=%s Port=%s User=%s",
                    bool(BRIGHTDATA_HOST), bool(BRIGHTDATA_PORT), bool(BRIGHTDATA_USERNAME))
        return None

    proxy_url = f"http://{BRIGHTDATA_USERNAME}:{BRIGHTDATA_PASSWORD}@{BRIGHTDATA_HOST}:{BRIGHTDATA_PORT}"
    log.info("Proxy configured: %s:%s", BRIGHTDATA_HOST, BRIGHTDATA_PORT)
    return {
        'http': proxy_url,
        'https': proxy_url
    }


def fetch_html_content(url: str) -> str:
    """Fetches the HTML content for a given product."""
    if not isinstance(url, str):
        raise TypeError("URL must be a string.")
    try:
        proxies = get_proxy_dict()
        use_proxy = proxies is not None

        if use_proxy:
            log.info("Using Bright Data ISP proxy for request to %s", url)

        response = requests.get(url, impersonate="chrome",
                                timeout=30, proxies=proxies)
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


def extract_product_name(soup: BeautifulSoup) -> str:
    """Extracts the name of the product from the parsed HTML."""
    og_title = soup.find('meta', property='og:title')
    if og_title:
        product_name = og_title.get("content")
        log.debug("Extracted product name successfully: %s", product_name)
        return product_name.strip()

    log.warning("Product name not found.")
    return None


def extract_current_price(soup: BeautifulSoup) -> str:
    """Extracts the current price of the product from the parsed HTML."""
    price_span = soup.main.find(
        "span", attrs={"data-price-type": "finalPrice"})
    if price_span:
        price = price_span.find("span", class_="price")
        log.debug("Extracted current price successfully: %s",
                  price.text.strip())
        return price.text.strip()

    log.warning("Current price not found.")
    return None


def extract_original_price(soup: BeautifulSoup) -> str:
    """Extracts the original price of the product from the parsed HTML."""
    price_span = soup.main.find("span", attrs={"data-price-type": "oldPrice"})
    if price_span:
        original_price = price_span.find("span", class_="price")
        log.debug("Extracted original price successfully: %s",
                  original_price.text.strip())
        return original_price.text.strip()

    log.warning(
        "HTML tag for original price not found; current price identified as original price.")
    return extract_current_price(soup)


def extract_currency_code(soup: BeautifulSoup) -> str:
    """Extracts the currency code of the product from the parsed HTML."""
    currency_meta = soup.find('meta', property='product:price:currency')
    if currency_meta:
        currency = currency_meta.get('content')
        log.debug("Extracted currency code successfully: %s", currency)
        return currency.strip()

    log.warning("Currency code not found in HTML.")
    return None


def extract_website_name(url: str, soup: BeautifulSoup) -> str:
    """Extracts the name of the website from the parsed HTML."""
    og_site = soup.find('meta', property='og:site_name')
    if og_site:
        log.debug("Extracted website name from HTML successfully: %s",
                  og_site.get('content'))
        return og_site.get('content').strip().lower()

    match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+)\.', url)
    if match:
        log.debug("Extracted website name from URL successfully: %s",
                  match.group(1))
        return match.group(1).lower()

    log.warning("Website name not found in HTML; unable to extract from URL.")
    return None


def extract_all_product_info(url: str, soup: BeautifulSoup) -> dict:
    """For existing URLs, extracts and returns relevant data for each product as a dictionary."""
    return {
        "url": url,
        "product_name": extract_product_name(soup),
        "current_price": extract_current_price(soup),
        "original_price": extract_original_price(soup),
        "currency_code": extract_currency_code(soup),
        "website_name": extract_website_name(url, soup),
        "page_exists": True,
        "scraped_at": datetime.now().isoformat()
    }


def create_product_info_not_found(url: str) -> dict:
    """Creates product dictionary when page doesn't exist (404)."""
    return {
        "url": url,
        "product_name": None,
        "current_price": None,
        "original_price": None,
        "currency_code": None,
        "website_name": None,
        "page_exists": False,
        "scraped_at": None
    }


def scrape_all_products(urls: list) -> list[dict]:
    """Scrapes information on all products from a given list of URLs."""
    if not isinstance(urls, list):
        raise TypeError("Must pass a list of URLs.")

    log.info("Starting to scrape %d products", len(urls))
    products = []

    for url in urls:
        try:
            response = fetch_html_content(url)

            if response is None:  # Page doesn't exist anymore (404)
                product_info = create_product_info_not_found(url)
            else:
                soup = parse_html_content(response)
                product_info = extract_all_product_info(url, soup)
                log.info(
                    "Successfully scraped product information from URL: %s", url)
            products.append(product_info)

        except Exception as e:
            log.error("Failed to scrape URL: %s - %s", url, e)

    return products


if __name__ == "__main__":
    # Example usage
    urls = [
        "https://www.awd-it.co.uk/awd-lian-li-o11-mini-snow-edition-ryzen-5-5600x-4.6ghz-gigabyte-b550-vison-nvidia-geforce-rtx-3060-vision-12gb-gaming-pc.html"
    ]

    scraped_products = scrape_all_products(urls)
    for product in scraped_products:
        print(product)
