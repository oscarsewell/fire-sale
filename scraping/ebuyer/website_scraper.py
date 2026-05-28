"""A script to scrape price and product data from the HTML content on a website."""

import re
from datetime import datetime
from curl_cffi import requests
from bs4 import BeautifulSoup


def fetch_html_content(url: str) -> str:
    """Fetches the HTML content for a given product."""
    if not isinstance(url, str):
        raise TypeError(f"URL must be a string.")

    try:
        response = requests.get(url, impersonate="chrome", timeout=10)
        response.raise_for_status()
        print(f"Successfully fetched HTML content from URL: {url}")
    except requests.RequestException as e:
        print(f"Failed to fetch HTML content from URL: {url} - {e}")
        raise

    return response.text


def parse_html_content(content: str) -> BeautifulSoup:
    """Parses the HTML content for that product."""
    soup = BeautifulSoup(content, 'html.parser')
    print("Parsed HTML content successfully.")
    return soup


def extract_product_name(soup: BeautifulSoup) -> str:
    """Extracts the name of the product from the parsed HTML."""
    og_title = soup.find('meta', property='og:title')
    if og_title:
        product_name = og_title.get("content")
        print(f"Extracted product name successfully: {product_name}")
        return product_name.strip()
    else:
        print("Product name not found.")
        return "N/A"


def extract_current_price(soup: BeautifulSoup) -> str:
    """Extracts the current price of the product from the parsed HTML."""
    price = soup.find("span", id="lblSellingPrice")
    if price:
        print(f"Extracted current price successfully: {price.text.strip()}")
        return price.text.strip()
    else:
        print("Current price not found.")
        return "N/A"


def extract_original_price(soup: BeautifulSoup) -> str:
    """Extracts the original price of the product from the parsed HTML."""
    original_price = soup.find('span', id='lblTicketPrice')

    if original_price:
        print(f"Extracted original price successfully: {original_price.text.strip()}")
        return original_price.text.strip()
    else:
        print("HTML tag for original price not found; current price identified as original price.")
        return extract_current_price(soup)


def extract_website_name(url: str, soup: BeautifulSoup) -> str:
    """Extracts the name of the website from the parsed HTML."""
    og_site = soup.find('meta', property='og:site_name')
    if og_site:
        print(f"Extracted website name from HTML successfully: {og_site.get('content')}")
        return og_site.get('content').strip().lower()
    else:
        match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+)\.', url)
        if match:
            print(f"Extracted website name from URL successfully: {match.group(1)}")
            return match.group(1).lower()
        
        print("Website name not found in HTML; unable to extract from URL.")
        return "N/A"


def extract_all_product_info(url: str, soup: BeautifulSoup) -> dict:    
    """Extracts and returns relevant data for each product as a dictionary."""
    return {  
        "product_name": extract_product_name(soup), 
        "current_price": extract_current_price(soup),
        "original_price": extract_original_price(soup),
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
            print(f"Successfully scraped product information from URL: {url}")
        
        except Exception as e:
            print(f"Failed to scrape URL: {url} - {e}")
    
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

    website_name = extract_website_name(urls[0], parsed_content)
    print(f"Website Name: {website_name}")

    scraped_products = scrape_all_products(urls)
    for product in scraped_products:
        print(product)
