# pylint: disable = redefined-outer-name
"""A script to scrape price and product data from the HTML content on a website."""

import logging
from datetime import datetime
from curl_cffi import requests
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
    except requests.RequestException as e:
        log.error("Failed to fetch HTML content from URL: %s: %s", url, e)
        raise

    return response.text


def parse_html_content(content: str) -> BeautifulSoup:
    """Parses the HTML content for that product."""
    soup = BeautifulSoup(content, 'html.parser')
    log.debug("Parsed HTML content successfully.")
    return soup


def extract_current_price(soup: BeautifulSoup) -> str:
    """Extracts the current price of the product from the parsed HTML."""
    price = soup.find("span", attrs={"data-qa": "price-current"})
    if price:
        log.debug("Extracted current price successfully: %s", price.text.strip())
        return price.text.strip()

    log.warning("Current price not found.")
    return "N/A"


def extract_currency_code(soup: BeautifulSoup) -> str:
    """Extracts the currency code of the product from the parsed HTML."""
    currency_meta = soup.find('meta', property='product:price:currency')
    if currency_meta:
        currency = currency_meta.get('content')
        log.debug("Extracted currency code successfully: %s", currency)
        return currency.strip()

    log.warning("Currency code not found in HTML.")
    return "N/A"


def extract_all_product_info(url: str, soup: BeautifulSoup) -> dict:
    """Extracts and returns relevant data for each product as a dictionary."""
    return {
        "url": url, 
        "current_price": extract_current_price(soup),
        "currency_code": extract_currency_code(soup),
        "scraped_at": datetime.now().isoformat()
    }


def scrape_all_products(urls: list[tuple]) -> list[dict]:
    """Scrapes information on all products from a given list of URLs."""
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
            log.error("Failed to scrape URL: %s - %s", url, e)

    return products


if __name__ == "__main__":
    # Example usage
    urls = [
        "https://www.overclockers.co.uk/medion-erazer-crawler-e30e-nvidia-rtx-2050-16gb-15.6-fhd-intel-i5-13420h-ga-lap-mdn-05630.html"
    ]

    html_content = fetch_html_content(urls[0])
    parsed_content = parse_html_content(html_content)

    url = urls[0]
    print(f"URL: {url}")

    current_price = extract_current_price(parsed_content)
    print(f"Current Price: {current_price}")

    currency_code = extract_currency_code(parsed_content)
    print(f"Currency Code: {currency_code}")

    scraped_products = scrape_all_products(urls)
    for product in scraped_products:
        print(product)
