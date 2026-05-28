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
    # Structure of prices needs to be altered to reflect the given website
    return """
    <html>
        <head>
            <meta property="og:site_name" content="Store"/>
            <meta property="og:title" content="Gaming Laptop"/>
        </head>
        <body>
            <span class="price">
                <small>$</small>99.<small>99</small>
            </span>
            <span class="wasPrice rrpPrice">
                <span class="was" title="Recommended Retail Price">RRP:</span>
                    <small>$</small>199.<small>99</small>
            </span>
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
        </head>
        <body>
            <span class="price">
                <small>$</small>300.<small>00</small>
            </span>
        </body>
    </html>
    """


@pytest.fixture
def mock_html_content_with_whitespace():
    """Fixture for mock HTML content with whitespace around all values."""
    return """
    <html>
        <head>
            <meta property="og:site_name" content="  Store With Spaces  "/>
            <meta property="og:title" content="  Gaming Laptop Pro  "/>
        </head>
        <body>
            <span class="price">
                <small>$</small>50.<small>00</small>
            </span>
            <span class="wasPrice rrpPrice">
                <span class="was" title="Recommended Retail Price">RRP:</span>
                    <small>$</small>400.<small>00</small>
            </span>
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
    with patch("scan_scraper.fetch_html_content") as mock_fetch, \
         patch("scan_scraper.parse_html_content") as mock_parse:
        # To handle multiple URLs
        mock_fetch.side_effect = [mock_html_content, mock_html_content_no_original_price]
        mock_parse.side_effect = [mock_soup, mock_soup_no_original_price]
        yield mock_fetch, mock_parse
