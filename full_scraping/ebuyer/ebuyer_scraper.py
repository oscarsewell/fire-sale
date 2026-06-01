# pylint: disable = redefined-outer-name
"""A script to scrape price and product data from the HTML content on a website."""

import json
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
        response.raise_for_status()
        log.debug("Successfully fetched HTML content from URL: %s", url)
    except RequestException as e:
        log.error("Failed to fetch HTML content from URL: %s", url, e)
        raise

    return response.text


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
    return "N/A"


def extract_current_price(soup: BeautifulSoup) -> str:
    """Extracts the current price of the product from the parsed HTML."""
    price = soup.find("span", id="lblSellingPrice")
    if price:
        log.debug("Extracted current price successfully: %s", price.text.strip())
        return price.text.strip()

    log.warning("Current price not found.")
    return "N/A"


def extract_original_price(soup: BeautifulSoup) -> str:
    """Extracts the original price of the product from the parsed HTML."""
    original_price = soup.find('span', id='lblTicketPrice')

    if original_price:
        log.debug("Extracted original price successfully: %s", original_price.text.strip())
        return original_price.text.strip()

    log.warning("HTML tag for original price not found; current price identified as original price.")
    return extract_current_price(soup)


def extract_currency_code(soup: BeautifulSoup) -> str:
    """Extracts the currency code from the structured data."""
    script = soup.find("script", id="structuredDataLdJson")
    if not script:
        log.warning("Currency code script tag not found.")
        return "N/A"
    
    data = json.loads(script.string)
    if isinstance(data, list):
        data = data[0]
    
    currency = data.get('offers')[0].get('priceCurrency')
    log.debug("Extracted currency code successfully: %s", currency)
    return currency


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
    return "N/A"


def extract_all_product_info(url: str, soup: BeautifulSoup) -> dict:
    """Extracts and returns relevant data for each product as a dictionary."""
    return {
        "product_name": extract_product_name(soup), 
        "current_price": extract_current_price(soup),
        "original_price": extract_original_price(soup),
        "currency_code": extract_currency_code(soup),
        "url": url, 
        "website_name": extract_website_name(url, soup), 
        "scraped_at": datetime.now().isoformat()
    }

def scrape_all_products(urls: list[str]) -> list[dict]:
    """Scrapes information on all products from a given list of URLs."""
    # The script which passes list of URLs to this function should handle: empty list, None
    if not isinstance(urls, list):
        raise TypeError("Must pass a list of URLs.")

    log.info(f"Starting to scrape {len(urls)} products")
    products = []

    for url in urls:
        try:
            response = fetch_html_content(url)
            soup = parse_html_content(response)
            product_info = extract_all_product_info(url, soup)
            products.append(product_info)
            log.info("Successfully scraped product information from URL: %s", url)
        except Exception as e:
            log.error("Failed to scrape URL: %s", url, e)

    return products


if __name__ == "__main__":
    # Example usage
    urls = [
        "https://www.ebuyer.com/msi-msi-katana-15-inch-gaming-laptop---intel-core-i7-16gb-512gb-ssd-rtx-5060-705530#colcode=70553003"
    ]

    html_content = fetch_html_content(urls[0])
    parsed_content = parse_html_content(html_content)

    product_name = extract_product_name(parsed_content)
    print(f"Product Name: {product_name}")

    current_price = extract_current_price(parsed_content)
    print(f"Current Price: {current_price}")

    original_price = extract_original_price(parsed_content)
    print(f"Original Price: {original_price}")

    currency_code = extract_currency_code(parsed_content)
    print(f"Currency Code: {currency_code}")

    website_name = extract_website_name(urls[0], parsed_content)
    print(f"Website Name: {website_name}")

    scraped_products = scrape_all_products(urls)
    for product in scraped_products:
        print(product)
