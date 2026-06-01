# pylint: disable = redefined-outer-name
"""A script to scrape price and product data from the HTML content on a website."""

import logging
import re
from datetime import datetime
from curl_cffi import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

log = logging.getLogger(__name__)


def fetch_html_content(url: str) -> str:
    """Fetches the HTML content for a given product."""
    if not isinstance(url, str):
        raise TypeError("URL must be a string.")

    try:
        response = requests.get(url, impersonate="chrome", timeout=10)
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
    price = soup.find("span", attrs={"data-qa": "price-current"})
    if price:
        log.debug("Extracted current price successfully: %s", price.text.strip())
        return price.text.strip()

    log.warning("Current price not found.")
    return None


def extract_original_price(soup: BeautifulSoup) -> str:
    """Extracts the original price of the product from the parsed HTML."""
    original_price = soup.find("span", attrs={"data-qa": "price-original"})

    if original_price:
        log.debug("Extracted original price successfully: %s", original_price.text.strip())
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
        log.debug("Extracted website name from HTML successfully: %s", og_site.get('content'))
        return og_site.get('content').strip().lower()

    match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+)\.', url)
    if match:
        log.debug("Extracted website name from URL successfully: %s", match.group(1))
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

            if response is None: # Page doesn't exist anymore (404)
                product_info = create_product_info_not_found(url)
            else:
                soup = parse_html_content(response)
                product_info = extract_all_product_info(url, soup)
                log.info("Successfully scraped product information from URL: %s", url)
            products.append(product_info)

        except Exception as e:
            log.error("Failed to scrape URL: %s - %s", url, e)

    return products


if __name__ == "__main__":
    # Example usage
    urls = [
        "https://www.overclockers.co.uk/medion-erazer-crawler-e30e-nvidia-rtx-2050-16gb-15.6-fhd-intel-i5-13420h-ga-lap-mdn-05630.html"
    ]

    scraped_products = scrape_all_products(urls)
    for product in scraped_products:
        print(product)
