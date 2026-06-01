"""Fixtures for tests in the scraping phase."""

from unittest.mock import patch
import pytest
from bs4 import BeautifulSoup


@pytest.fixture
def valid_urls():
    """Fixture for a list of URLs, each for a different product on the same website."""
    return [
        "https://www.store.com/product1",
        "https://www.store.com/product2"    
    ]


@pytest.fixture
def valid_url():
    """Fixture for a single product URL."""
    return "https://www.store.com/product1"



@pytest.fixture
def mock_html_content():
    """Fixture for mock HTML content."""
    return """
    <html>
        <head>
            <meta property="og:title" content="Gaming Laptop"/>
            <meta property="product:price:currency" content="USD"/>
        </head>
        <body>
            <main>
                <span data-price-type="finalPrice" class="price-wrapper price-including-tax">
                    <span class="price">$99.99</span>
                </span>
                <span data-price-type="oldPrice" class="price-wrapper price-including-tax">
                    <span class="price">$199.99</span>
                </span>
            </main>
        </body>
    </html>
    """


@pytest.fixture
def mock_html_content_no_original_price():
    """Fixture for mock HTML content without original price."""
    return """
    <html>
        <head>
            <meta property="og:title" content="Home Laptop"/>
            <meta property="product:price:currency" content="USD"/>
        </head>
        <body>
            <main>
                <span data-price-type="finalPrice" class="price-wrapper price-including-tax">
                    <span class="price">$300.00</span>
                </span>
            </main>
        </body>
    </html>
    """


@pytest.fixture
def mock_html_content_with_whitespace():
    """Fixture for mock HTML content with whitespace around all values."""
    return """
    <html>
        <head>
            <meta property="og:title" content="  Gaming Laptop Pro  "/>
            <meta property="product:price:currency" content="  USD  "/>
        </head>
        <body>
            <main>
                <span data-price-type="finalPrice" class="price-wrapper price-including-tax">
                    <span class="price">  $50.00  </span>
                </span>
                <span data-price-type="oldPrice" class="price-wrapper price-including-tax">
                    <span class="price">  $400.00  </span>
                </span>
            </main>
        </body>
    </html>
    """


@pytest.fixture
def mock_soup(mock_html_content):
    """Fixture for a BeautifulSoup object parsed from mock HTML."""
    return BeautifulSoup(mock_html_content, 'html.parser')


@pytest.fixture
def mock_soup_no_original_price(mock_html_content_no_original_price):
    """Fixture for a BeautifulSoup object without original price."""
    return BeautifulSoup(mock_html_content_no_original_price, 'html.parser')


@pytest.fixture
def mock_soup_with_whitespace(mock_html_content_with_whitespace):
    """Fixture for a BeautifulSoup object with whitespace-padded values."""
    return BeautifulSoup(mock_html_content_with_whitespace, 'html.parser')


@pytest.fixture
def mock_scraper_functions(mock_html_content, mock_soup, mock_html_content_no_original_price, 
                           mock_soup_no_original_price):
    """Fixture that patches and pre-configures scraper functions."""
    with patch("awd_it_full_scraper.fetch_html_content") as mock_fetch, \
         patch("awd_it_full_scraper.parse_html_content") as mock_parse:
        # To handle multiple URLs
        mock_fetch.side_effect = [mock_html_content, mock_html_content_no_original_price]
        mock_parse.side_effect = [mock_soup, mock_soup_no_original_price]
        yield mock_fetch, mock_parse
