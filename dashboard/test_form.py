"""Tests for the Dashboard form page using Streamlit's AppTest class."""

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def form():
    """Fixture that creates and runs the form page."""
    at = AppTest.from_file("form.py")
    at.run()
    return at


# Rendering
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
    form.text_input[0].set_value("https://example.com/product")
    form.number_input[0].set_value(50)
    form.button[0].click()
    form.run()
    assert "Now tracking this product at a £50 target discount" in form.success[0].value


def test_submit_high_discount(form):
    """Tests that high discount values are accepted."""
    form.text_input[0].set_value("https://example.com/product")
    form.number_input[0].set_value(1999)
    form.button[0].click()
    form.run()
    assert "Now tracking this product at a £1999 target discount" in form.success[0].value


# Form submission error
def test_submit_empty_url_shows_error_message(form):
    """Tests that submitting an empty URL shows error message."""
    form.text_input[0].set_value("") # empty url
    form.number_input[0].set_value(50)
    form.button[0].click()
    form.run()
    assert "Please enter a valid URL and discount" in form.error[0].value


def test_submit_zero_discount_shows_error_message(form):
    """Tests that submitting a target discount of £0 shows error message."""
    form.text_input[0].set_value("https://example.com/product")
    form.number_input[0].set_value(0) # target discount of £0
    form.button[0].click()
    form.run()
    assert "Please enter a valid URL and discount" in form.error[0].value


def test_submit_both_fields_empty_shows_error(form):
    """Tests that submitting with both fields empty shows error message."""
    form.text_input[0].set_value("")
    form.number_input[0].set_value(0)
    form.button[0].click()
    form.run()
    assert "Please enter a valid URL and discount" in form.error[0].value
