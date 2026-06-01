# pylint: disable = unused-argument, redefined-outer-name
"""Tests for the website scraping script."""

from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest
from bs4 import BeautifulSoup
from awd_it_scraper import (
    fetch_html_content,
    parse_html_content,
    extract_current_price,
    extract_currency_code,
    extract_all_product_info,
    scrape_all_products,
)

class TestFetchHTMLContent:
    """Test cases for fetching HTML content from URLs."""

    @patch("awd_it_scraper.requests.get")
    def test_fetch_html_content_success(self, mock_get, valid_url):
        """Test successful HTML content fetching."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_get.return_value = mock_response

        result = fetch_html_content(valid_url)
        assert isinstance(result, str)
        assert "<html>" in result
        mock_get.assert_called_once_with(valid_url, impersonate="chrome", timeout=10)

    @patch("awd_it_scraper.requests.get")
    def test_fetch_html_content_raises_on_bad_status(self, mock_get, valid_url):
        """Test that fetch_html_content raises error on bad HTTP status."""
        mock_get.return_value.raise_for_status.side_effect = Exception("404 Not Found")
        with pytest.raises(Exception):
            fetch_html_content(valid_url)

    def test_fetch_html_content_invalid_none(self):
        """Test that fetch_html_content raises TypeError when given a NULL URL."""
        with pytest.raises(TypeError):
            fetch_html_content(None)


class TestParseHTMLContent:
    """Test cases for parsing HTML content."""

    def test_parse_html_content_returns_soup(self, mock_html_content):
        """Test that parse_html_content returns a BeautifulSoup object for valid HTML content."""
        result = parse_html_content(mock_html_content)
        assert isinstance(result, BeautifulSoup)

    def test_parse_html_content_parses_correctly(self, mock_html_content):
        """Test that parse_html_content correctly parses HTML."""
        soup = parse_html_content(mock_html_content)
        assert soup.find('meta', property='og:title')['content'] == "Gaming Laptop"

        price_span = soup.main.find("span", attrs={"data-price-type": "finalPrice"})
        if price_span:
            assert price_span.find("span", class_="price").text.strip() == "$99.99"

    @pytest.mark.parametrize("invalid_content", ["", "<incomplete>"])
    def test_parse_html_content_edge_cases(self, invalid_content):
        """Test that parse_html_content handles edge cases for HTML content."""
        result = parse_html_content(invalid_content)
        assert isinstance(result, BeautifulSoup)


class TestExtractCurrentPrice:
    """Test cases for extracting current price."""

    def test_extract_current_price_success(self, mock_soup):
        """Tests for successful current price extraction."""
        result = extract_current_price(mock_soup)
        assert result == "$99.99"

    def test_extract_current_price_returns_string(self, mock_soup):
        """Test that extract_current_price returns a string."""
        result = extract_current_price(mock_soup)
        assert isinstance(result, str)

    def test_extract_current_price_strips_whitespace(self, mock_soup_with_whitespace):
        """Test that extract_current_price strips whitespace."""
        result = extract_current_price(mock_soup_with_whitespace)
        assert result == "$50.00"


class TestExtractCurrencyCode:
    """Test cases for extracting currency code."""

    def test_extract_currency_code_success(self, mock_soup):
        """Test successful currency code extraction."""
        result = extract_currency_code(mock_soup)
        assert result == "USD"

    def test_extract_currency_code_returns_string(self, mock_soup):
        """Test that extract_currency_code returns a string."""
        result = extract_currency_code(mock_soup)
        assert isinstance(result, str)

    def test_extract_currency_code_returns_na_when_missing(self):
        """Test that extract_currency_code returns 'N/A' when element missing."""
        html = "<html><body>Test</body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        result = extract_currency_code(soup)
        assert result == "N/A"


class TestExtractAllProductInfo:
    """Test cases for extracting all product information."""

    def test_extract_all_product_info_returns_dict(self, valid_url, mock_soup):
        """Test that extract_all_product_info returns a dictionary."""
        result = extract_all_product_info(valid_url, mock_soup)
        assert isinstance(result, dict)

    def test_extract_all_product_info_contains_required_keys(self, valid_url, mock_soup):
        """Test that extract_all_product_info contains all required keys."""
        result = extract_all_product_info(valid_url, mock_soup)
        required_keys = {
            "url",
            "current_price",
            "currency_code",
            "scraped_at"
        }
        assert set(result.keys()) == required_keys

    def test_extract_all_product_info_values_correct(self, valid_url, mock_soup):
        """Test that extract_all_product_info extracts correct values."""
        result = extract_all_product_info(valid_url, mock_soup)
        assert result["url"] == valid_url
        assert result["current_price"] == "$99.99"
        assert result["currency_code"] == "USD"

    def test_extract_all_product_info_includes_timestamp(self, valid_url, mock_soup):
        """Test that extract_all_product_info includes scraped_at timestamp."""
        result = extract_all_product_info(valid_url, mock_soup)
        assert "scraped_at" in result

        scraped_at = datetime.fromisoformat(result["scraped_at"])
        assert isinstance(scraped_at, datetime)


class TestScrapeAllProducts:
    """Test cases for scraping multiple products."""

    def test_scrape_all_products_returns_list(self, mock_scraper_functions, valid_urls):
        """Test that scrape_all_products returns a list.""" 
        result = scrape_all_products(valid_urls)
        assert isinstance(result, list)

    def test_scrape_all_products_correct_count(self, mock_scraper_functions, valid_urls):
        """Test that scrape_all_products returns correct number of products."""  
        result = scrape_all_products(valid_urls)
        assert len(result) == len(valid_urls)

    def test_scrape_all_products_contains_correct_data(self, mock_scraper_functions, valid_urls):
        """Test that scrape_all_products contains correct product data."""
        result = scrape_all_products(valid_urls)
        # 1st URL
        assert result[0]["url"] == valid_urls[0]
        assert result[0]["current_price"] == "$99.99"
        assert result[0]["currency_code"] == "USD"

        # 2nd URL
        assert result[1]["url"] == valid_urls[1]
        assert result[1]["current_price"] == "$300.00"
        assert result[1]["currency_code"] == "USD"

    def test_scrape_all_products_empty_list(self):
        """Test that scrape_all_products handles empty URL list."""
        result = scrape_all_products([])
        assert result == []

    def test_scrape_all_products_invalid_type(self):
        """Test that scrape_all_products raises error when given None (e.g a failed DB query)."""
        with pytest.raises(TypeError):
            scrape_all_products(None)
