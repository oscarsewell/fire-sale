"""Fixtures for tests in the scraping phase."""

from unittest.mock import patch
import pytest
from bs4 import BeautifulSoup


@pytest.fixture
def valid_urls_and_ids():
    """Fixture for a list of tuples containing URLs and IDs, 
    each for a different product on the same website."""
    return [
        ("https://www.store.com/product1", 1),
        ("https://www.store.com/product2", 2)
    ]


@pytest.fixture
def valid_url_and_id():
    """Fixture for a single product URL and ID."""
    return ("https://www.store.com/product1", 1)


@pytest.fixture
def mock_html_content():
    """Fixture for mock HTML content."""
    return """
    <html>
        <head>
            <meta property="og:site_name" content="Store"/>
            <meta property="og:title" content="Gaming Laptop"/>
        </head>
        <body>
            <span id="lblSellingPrice">$99.99</span>
            <span id="lblTicketPrice">$199.99</span>
            <script id="structuredDataLdJson" type="application/ld+json">[{
                "offers": [{
                    "priceCurrency": "USD"
                }]
            }]</script>
        </body>
    </html>
    """


@pytest.fixture
def mock_html_content_no_original_price():
    """Fixture for mock HTML content without original price."""
    return """
    <html>
        <head>
            <meta property="og:site_name" content="Store"/>
            <meta property="og:title" content="Home Laptop"/>
        </head>
        <body>
            <span id="lblSellingPrice">$300.00</span>
            <script id="structuredDataLdJson" type="application/ld+json">[{
                "offers": [{
                    "priceCurrency": "USD"
                }]
            }]</script>
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
            <span id="lblSellingPrice">  $50.00  </span>
            <span id="lblTicketPrice">  $400.00  </span>
            <script id="structuredDataLdJson" type="application/ld+json">[{
                "offers": [{
                    "priceCurrency": "USD"
                }]
            }]</script>
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
    with patch("ebuyer_scraper.fetch_html_content") as mock_fetch, \
         patch("ebuyer_scraper.parse_html_content") as mock_parse:
        # To handle multiple URLs
        mock_fetch.side_effect = [mock_html_content, mock_html_content_no_original_price]
        mock_parse.side_effect = [mock_soup, mock_soup_no_original_price]
        yield mock_fetch, mock_parse
