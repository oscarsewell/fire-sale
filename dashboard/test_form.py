"""Tests for the Dashboard form page using Streamlit's AppTest class."""

import pytest
from streamlit.testing.v1 import AppTest
from form import (
    extract_website_name, 
    is_website_supported, 
    check_url_scrapable,
    get_scraper_path
)


@pytest.fixture
def form():
    """Fixture that creates and runs the form page."""
    at = AppTest.from_file("form.py")
    at.run()
    return at


# Check rendering
def test_form_page_renders(form):
    """Tests that the form page renders without errors and contains the expected input fields."""
    assert len(form.text_input) == 1
    assert len(form.number_input) == 1
    assert len(form.button) == 1


# Verifying displayed content
def test_form_title_displays(form):
    """Tests that the page title 'Product Tracking Form' is displayed."""
    assert "Product Tracking Form" in form.title[0].value


def test_form_description_displays(form):
    """Tests that the form description is displayed."""
    assert "Add a new product to track" in form.markdown[0].value


def test_url_input_has_correct_placeholder(form):
    """Tests that URL input field has the expected placeholder text."""
    assert form.text_input[0].placeholder == "https://website.com/product"


def test_discount_input_default_value(form):
    """Tests that discount field defaults to 0."""
    assert form.number_input[0].value == 0


# Form submission success
def test_submit_valid_product_shows_success_message(form):
    """Tests that submitting a valid product URL and discount shows the success message."""
    form.text_input[0].set_value("https://awd-it.co.uk/product")
    form.number_input[0].set_value(50)
    form.button[0].click()
    form.run()
    assert "Success! Now tracking this product at a £50 target discount" in form.success[0].value


def test_submit_high_discount(form):
    """Tests that high discount values are accepted."""
    form.text_input[0].set_value("https://awd-it.co.uk/product")
    form.number_input[0].set_value(1999)
    form.button[0].click()
    form.run()
    assert "Success! Now tracking this product at a £1999 target discount" in form.success[0].value


@pytest.mark.parametrize("valid_url", [
    "awd-it.co.uk/product",
    "www.ebuyer.com/product",
    "https://overclockers.co.uk/product#anchor",
    "https://overclockers.co.uk/product?id=123&color=red",
])
def test_submit_various_valid_urls_shows_success_message(form, valid_url):
    """Tests that various valid URL formats are accepted."""
    form.text_input[0].set_value(valid_url)
    form.number_input[0].set_value(50)
    form.button[0].click()
    form.run()
    assert "Success! Now tracking this product at a £50 target discount" in form.success[0].value


# Form submission error
@pytest.mark.parametrize("invalid_url", [
    "",
    "not a url",
    "https://example",
    "https://example<>.com",
    "https://amazon.com/product",
])
def test_submit_invalid_urls_shows_error_message(form, invalid_url):
    """Tests that submitting an empty URL shows error message."""
    form.text_input[0].set_value(invalid_url)
    form.number_input[0].set_value(50)
    form.button[0].click()
    form.run()
    assert "Please enter a valid URL from our supported websites" in form.error[0].value


def test_submit_zero_discount_shows_error_message(form):
    """Tests that submitting a target discount of £0 shows error message."""
    form.text_input[0].set_value("https://example.com/product")
    form.number_input[0].set_value(0) # target discount of £0
    form.button[0].click()
    form.run()
    assert "Please enter a valid URL from our supported websites" in form.error[0].value


def test_submit_both_fields_empty_shows_error(form):
    """Tests that submitting with both fields empty shows error message."""
    form.text_input[0].set_value("")
    form.number_input[0].set_value(0)
    form.button[0].click()
    form.run()
    assert "Please enter a valid URL from our supported websites" in form.error[0].value


# Tests for URL parsing and validation
def test_extract_website_name_with_https():
    """Tests extracting domain from URL with https."""
    assert extract_website_name("https://awd-it.co.uk/product") == "awd-it"
    assert extract_website_name("https://ebuyer.com/product") == "ebuyer"


def test_extract_website_name_with_www():
    """Tests extracting domain from URL with www prefix."""
    assert extract_website_name("www.overclockers.co.uk/product") == "overclockers"


def test_extract_website_name_without_scheme():
    """Tests extracting domain from URL without scheme."""
    assert extract_website_name("awd-it.co.uk/product") == "awd-it"


def test_extract_website_name_returns_lowercase():
    """Tests that extracted domain is lowercase."""
    assert extract_website_name("https://AWD-IT.CO.UK/product") == "awd-it"


# Tests for website support
def test_is_website_supported_valid_domains():
    """Tests that supported websites are recognized."""
    assert is_website_supported("awd-it") == True
    assert is_website_supported("ebuyer") == True
    assert is_website_supported("overclockers") == True


def test_is_website_supported_invalid_domains():
    """Tests that unsupported websites are not recognized."""
    assert is_website_supported("amazon") == False
    assert is_website_supported("example") == False


# Tests for URL scrapability
def test_check_url_scrapable_valid_supported():
    """Tests that valid URLs from supported websites return the domain."""
    assert check_url_scrapable("https://awd-it.co.uk/product") == "awd-it"
    assert check_url_scrapable("https://ebuyer.com/product") == "ebuyer"


def test_check_url_scrapable_valid_unsupported():
    """Tests that valid URLs from unsupported websites return None."""
    assert check_url_scrapable("https://amazon.com/product") is None


def test_check_url_scrapable_invalid_url():
    """Tests that invalid URLs return None."""
    assert check_url_scrapable("not a url") is None
    assert check_url_scrapable("") is None


# Tests for scraper path generation
def test_get_scraper_path_awd_it():
    """Tests that awd-it domain maps to correct scraper path."""
    path = get_scraper_path("awd-it")
    assert "full_scraping/awd-it/awd_it_full_scraper.py" in path


def test_get_scraper_path_ebuyer():
    """Tests that ebuyer domain maps to correct scraper path."""
    path = get_scraper_path("ebuyer")
    assert "full_scraping/ebuyer/ebuyer_full_scraper.py" in path


def test_get_scraper_path_overclockers():
    """Tests that overclockers domain maps to correct scraper path."""
    path = get_scraper_path("overclockers")
    assert "full_scraping/overclockers/overclockers_full_scraper.py" in path


# Tests for multiple validation errors
def test_submit_invalid_url_and_discount_shows_both_errors(form):
    """Tests that both validation errors are shown when URL and discount are invalid."""
    form.text_input[0].set_value("https://amazon.com/product")
    form.number_input[0].set_value(0)
    form.button[0].click()
    form.run()
    assert len(form.error) == 2
    assert any("valid URL" in error.value for error in form.error)
    assert any("discount over £0" in error.value for error in form.error)


def test_submit_invalid_url_format_and_zero_discount_shows_both_errors(form):
    """Tests both errors are shown for invalid URL format and zero discount."""
    form.text_input[0].set_value("not a url")
    form.number_input[0].set_value(0)
    form.button[0].click()
    form.run()
    assert len(form.error) == 2
