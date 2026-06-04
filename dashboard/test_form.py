"""Tests for the Dashboard form page using Streamlit's AppTest class."""

import pytest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from form import (
    extract_website_name,
    is_website_supported,
    check_url_scrapable,
    get_scraper_path,
    track_product,
)


@pytest.fixture
def form():
    """Fixture that creates and runs the form page."""
    at = AppTest.from_file("form.py")
    at.session_state.user = {"id": 1}
    at.run()
    return at


# Check rendering
def test_form_page_renders(form):
    """Tests that form page renders with input fields."""
    assert len(form.text_input) >= 1
    assert len(form.number_input) >= 1
    assert len(form.button) >= 1


# Verifying displayed content
def test_form_title_displays(form):
    """Tests that the page title is displayed."""
    assert "Add a new product to track" in form.title[0].value


def test_url_input_has_correct_placeholder(form):
    """Tests that URL input field has the expected placeholder text."""
    text_inputs = form.text_input
    assert any(ti.placeholder == "https://website.com/product" for ti in text_inputs)


def test_discount_input_default_value(form):
    """Tests that discount field defaults to 0."""
    number_inputs = form.number_input
    assert any(ni.value == 0 for ni in number_inputs)


# Form submission: get elements
def get_form_element(form, element_type, index=0):
    """Helper to safely get form elements."""
    elements = getattr(form, element_type)
    if not elements:
        pytest.skip(f"No {element_type} elements found")
    return elements[index]


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
    url_input = get_form_element(form, "text_input", 0)
    discount_input = get_form_element(form, "number_input", 0)
    submit_btn = get_form_element(form, "button", 0)

    url_input.set_value(invalid_url)
    discount_input.set_value(50)
    submit_btn.click()
    form.run()

    assert any("Please enter a valid URL from our supported websites" in str(error.value) for error in form.error)


# ── track_product ─────────────────────────────────────────────────────────────

@patch("form.add_tracked_product")
@patch("form.upsert_product", return_value=1)
@patch("form.call_scraper")
def test_track_product_parses_string_price_into_pence(mock_scraper, mock_upsert, mock_add):
    """track_product should strip the currency symbol and convert price to pence."""
    mock_scraper.return_value = [{
        "page_exists": True,
        "product_name": "Test GPU",
        "current_price": "£749.99",
        "original_price": "£799.99",
        "currency_code": "GBP",
        "website_name": "ebuyer",
    }]
    with patch("form.st"):
        track_product("ebuyer", "https://ebuyer.com/p", 50, 1)

    mock_add.assert_called_once_with(1, 1, 69999, 74999)


@patch("form.call_scraper")
def test_track_product_shows_error_when_page_not_found(mock_scraper):
    """track_product should show an error when the scraper reports page_exists=False."""
    mock_scraper.return_value = [{"page_exists": False}]
    with patch("form.st") as mock_st:
        track_product("ebuyer", "https://ebuyer.com/p", 50, 1)

    mock_st.error.assert_called_once()
    assert "Could not retrieve product information" in mock_st.error.call_args[0][0]


def test_submit_zero_discount_shows_error_message(form):
    """Tests that submitting a target discount of £0 shows error message."""
    url_input = get_form_element(form, "text_input", 0)
    discount_input = get_form_element(form, "number_input", 0)
    submit_button = get_form_element(form, "button", 0)

    url_input.set_value("https://example.com/product")
    discount_input.set_value(0)  # target discount of £0
    submit_button.click()
    form.run()
    assert any("Please enter a valid URL from our supported websites" in str(error.value) for error in form.error)


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
    assert extract_website_name(
        "www.overclockers.co.uk/product") == "overclockers"


def test_extract_website_name_without_scheme():
    """Tests extracting domain from URL without scheme."""
    assert extract_website_name("awd-it.co.uk/product") == "awd-it"


def test_extract_website_name_returns_lowercase():
    """Tests that extracted domain is lowercase."""
    assert extract_website_name("https://AWD-IT.CO.UK/product") == "awd-it"


# Tests for website support
def test_is_website_supported_valid_domains():
    """Tests that supported websites are recognized."""
    assert is_website_supported("awd-it") is True
    assert is_website_supported("ebuyer") is True
    assert is_website_supported("overclockers") is True


def test_is_website_supported_invalid_domains():
    """Tests that unsupported websites are not recognized."""
    assert is_website_supported("amazon") is False
    assert is_website_supported("example") is False


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


def test_form_requires_user_id():
    """Tests that form() function requires user_id parameter."""
    from form import form
    with pytest.raises(TypeError):
        form()

# Form submission success
def test_submit_valid_url_no_validation_error(form):
    """Tests that a valid URL doesn't trigger validation error."""
    url_input = get_form_element(form, "text_input", 0)
    discount_input = get_form_element(form, "number_input", 0)
    submit_btn = get_form_element(form, "button", 0)

    url_input.set_value("https://awd-it.co.uk/product")
    discount_input.set_value(50)
    submit_btn.click()
    form.run()

    assert not any("Please enter a valid URL" in str(error.value) for error in form.error)