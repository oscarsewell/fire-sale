"""Routes product URLs to the correct copied scraper."""

import re
from urllib.parse import urlparse

from overclockers_scraper import scrape_all_products as scrape_overclockers
from ebuyer_scraper import scrape_all_products as scrape_ebuyer
from awd_it_scraper import scrape_all_products as scrape_awd_it


def clean_price(price):
    """Convert price string like '£1,299.99' into float."""
    if price is None:
        return None

    cleaned = re.sub(r"[^\d.]", "", str(price))

    if cleaned == "":
        return None

    return float(cleaned)


def get_domain(product_url):
    """Extract clean domain from product URL."""
    return urlparse(product_url).netloc.lower().replace("www.", "")


def normalise_scraped_product(scraped_product):
    """Convert scraper output into the format the Discord bot expects."""
    return {
        "product_url": scraped_product.get("url"),
        "product_name": scraped_product.get("product_name") or "Not set",
        "current_price": clean_price(scraped_product.get("current_price")),
        "original_price": clean_price(scraped_product.get("original_price")),
        "currency": scraped_product.get("currency_code") or "GBP",
        "site_name": scraped_product.get("website_name") or "Not set",
        "page_exists": scraped_product.get("page_exists", False),
        "scraped_at": scraped_product.get("scraped_at"),
    }


def full_scrape_product(product_url):
    """Run the correct full scraper for one product URL."""
    domain = get_domain(product_url)

    if domain == "overclockers.co.uk":
        results = scrape_overclockers([product_url])
    elif domain == "ebuyer.com":
        results = scrape_ebuyer([product_url])
    elif domain == "awd-it.co.uk":
        results = scrape_awd_it([product_url])
    else:
        raise ValueError(f"Unsupported product domain: {domain}")

    if not results:
        raise ValueError("No product data returned by scraper.")

    product_info = normalise_scraped_product(results[0])

    if not product_info["page_exists"]:
        raise ValueError("Product page does not exist.")

    return product_info
