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
    create_product_info_not_found,
    scrape_all_products
)


class TestFetchHTMLContent:
    """Test cases for fetching HTML content from URLs."""

    @patch("awd_it_scraper.requests.get")
    def test_fetch_html_content_success(self, mock_get, valid_url_and_id):
        """Test successful HTML content fetching."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_get.return_value = mock_response

        url, _ = valid_url_and_id
        result = fetch_html_content(url)
        assert isinstance(result, str)
        assert "<html>" in result
        mock_get.assert_called_once_with(url, impersonate="chrome", timeout=10)

    @patch("awd_it_scraper.requests.get")
    def test_fetch_html_content_404_returns_none(self, mock_get, valid_url_and_id):
        """Test that fetch_html_content returns None on 404 status."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        url, _ = valid_url_and_id
        result = fetch_html_content(url)
        assert result is None

    @patch("awd_it_scraper.requests.get")
    def test_fetch_html_content_server_error_raises(self, mock_get, valid_url_and_id):
        """Test that fetch_html_content raises on server errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_get.return_value = mock_response
        url, _ = valid_url_and_id
        with pytest.raises(Exception):
            fetch_html_content(url)

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
        assert result is None


class TestExtractAllProductInfo:
    """Test cases for extracting all product information."""

    def test_extract_all_product_info_returns_dict(self, valid_url_and_id, mock_soup):
        """Test that extract_all_product_info returns a dictionary."""
        url, product_id = valid_url_and_id
        result = extract_all_product_info(url, product_id, mock_soup)
        assert isinstance(result, dict)

    def test_extract_all_product_info_contains_required_keys(self, valid_url_and_id, mock_soup):
        """Test that extract_all_product_info contains all required keys."""
        url, product_id = valid_url_and_id
        result = extract_all_product_info(url, product_id, mock_soup)
        required_keys = {
            "product_id",
            "url",
            "current_price",
            "currency_code",
            "page_exists",
            "scraped_at"
        }
        assert set(result.keys()) == required_keys

    def test_extract_all_product_info_values_correct(self, valid_url_and_id, mock_soup):
        """Test that extract_all_product_info extracts correct values."""
        url, product_id = valid_url_and_id
        result = extract_all_product_info(url, product_id, mock_soup)
        assert result["product_id"] == product_id
        assert result["url"] == url
        assert result["current_price"] == "$99.99"
        assert result["currency_code"] == "USD"
        assert result["page_exists"] is True

    def test_extract_all_product_info_includes_timestamp(self, valid_url_and_id, mock_soup):
        """Test that extract_all_product_info includes scraped_at timestamp."""
        url, product_id = valid_url_and_id
        result = extract_all_product_info(url, product_id, mock_soup)
        assert "scraped_at" in result

        scraped_at = datetime.fromisoformat(result["scraped_at"])
        assert isinstance(scraped_at, datetime)


class TestCreateProductInfoNotFound:
    """Test cases for creating product info when page doesn't exist."""

    def test_create_product_info_not_found_returns_dict(self, valid_url_and_id):
        """Test that create_product_info_not_found returns a dictionary."""
        url, product_id = valid_url_and_id
        result = create_product_info_not_found(url, product_id)
        assert isinstance(result, dict)

    def test_create_product_info_not_found_contains_required_keys(self, valid_url_and_id):
        """Test that create_product_info_not_found contains all required keys."""
        url, product_id = valid_url_and_id
        result = create_product_info_not_found(url, product_id)
        required_keys = {
            "product_id",
            "url",
            "current_price",
            "currency_code",
            "page_exists",
            "scraped_at"
        }
        assert set(result.keys()) == required_keys

    def test_create_product_info_not_found_has_page_exists_false(self, valid_url_and_id):
        """Test that create_product_info_not_found sets page_exists to False."""
        url, product_id = valid_url_and_id
        result = create_product_info_not_found(url, product_id)
        assert result["page_exists"] is False

    def test_create_product_info_not_found_values_correct(self, valid_url_and_id):
        """Test that create_product_info_not_found sets correct values."""
        url, product_id = valid_url_and_id
        result = create_product_info_not_found(url, product_id)
        assert result["product_id"] == product_id
        assert result["url"] == url
        assert result["current_price"] is None
        assert result["currency_code"] is None
        assert result["scraped_at"] is None


class TestScrapeAllProducts:
    """Test cases for scraping multiple products."""

    def test_scrape_all_products_returns_list(self, mock_scraper_functions, valid_urls_and_ids):
        """Test that scrape_all_products returns a list.""" 
        result = scrape_all_products(valid_urls_and_ids)
        assert isinstance(result, list)

    def test_scrape_all_products_correct_count(self, mock_scraper_functions, valid_urls_and_ids):
        """Test that scrape_all_products returns correct number of products."""  
        result = scrape_all_products(valid_urls_and_ids)
        assert len(result) == len(valid_urls_and_ids)

    def test_scrape_all_products_contains_correct_data(self, mock_scraper_functions,
                                                       valid_urls_and_ids):
        """Test that scrape_all_products contains correct product data."""
        result = scrape_all_products(valid_urls_and_ids)
        # 1st URL
        assert result[0]["url"] == valid_urls_and_ids[0][0]
        assert result[0]["current_price"] == "$99.99"
        assert result[0]["currency_code"] == "USD"
        assert result[0]["page_exists"] is True

        # 2nd URL
        assert result[1]["url"] == valid_urls_and_ids[1][0]
        assert result[1]["current_price"] == "$300.00"
        assert result[1]["currency_code"] == "USD"
        assert result[1]["page_exists"] is True

    def test_scrape_all_products_empty_list(self):
        """Test that scrape_all_products handles empty URL list."""
        result = scrape_all_products([])
        assert result == []

    def test_scrape_all_products_invalid_type(self):
        """Test that scrape_all_products raises error when given None (e.g a failed DB query)."""
        with pytest.raises(TypeError):
            scrape_all_products(None)

    @patch("awd_it_scraper.requests.get")
    def test_scrape_all_products_handles_404_error(self, mock_get):
        """Test that scrape_all_products handles 404 errors gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        urls_and_ids = [("https://example.com/nonexistent", 1)]
        result = scrape_all_products(urls_and_ids)

        assert len(result) == 1
        assert result[0]["page_exists"] is False
        assert result[0]["current_price"] is None
        assert result[0]["currency_code"] is None
        assert result[0]["scraped_at"] is None
