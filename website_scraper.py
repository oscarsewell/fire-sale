# pylint: disable = unnecessary-pass, unused-import, unused-argument
"""A script to scrape price and product data from the HTML content on a website."""
from datetime import datetime
from bs4 import BeautifulSoup
import requests


def fetch_html_content(url: str) -> str:
    """Fetches the HTML content for a given product."""
    pass


def parse_html_content(content: str) -> BeautifulSoup:
    """Parses the HTML content for that product."""
    pass


def extract_product_name(soup: BeautifulSoup) -> str:
    """Extracts the name of the product from the parsed HTML."""
    pass


def extract_current_price(soup: BeautifulSoup) -> str:
    """Extracts the current price of the product from the parsed HTML."""
    pass


def extract_original_price(soup: BeautifulSoup) -> str:
    """Extracts the original price of the product from the parsed HTML."""
    pass


def extract_website_name(soup: BeautifulSoup) -> str:
    """Extracts the name of the website from the parsed HTML."""
    pass


def extract_all_product_info(url: str, soup: BeautifulSoup) -> dict:
    """Extracts and returns relevant data for each product as a dictionary."""
    pass


def scrape_all_products(urls: list[str]) -> list[dict]:
    """Scrapes information on all products from a given list of URLs."""
    pass
