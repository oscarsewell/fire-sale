"""Tests for the tracked products page."""

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def tracked_products_page():
    """Fixture that creates and runs the tracked products page."""
    at = AppTest.from_file("tracked_products.py")
    at.run()
    return at


def test_page_renders(tracked_products_page):
    """Tests that the tracked products page renders without errors."""
    assert tracked_products_page.title is not None


def test_page_has_title(tracked_products_page):
    """Tests that the page displays the title 'Your Tracked Products'."""
    assert len(tracked_products_page.title) > 0
    assert tracked_products_page.title[0].value == "Your Tracked Products"


def test_page_displays_description(tracked_products_page):
    """Tests that the page displays the description text."""
    assert "Products you are currently tracking:" in tracked_products_page.markdown[0].value


def test_page_shows_empty_state_message(tracked_products_page):
    """Tests that the page shows the 'No tracked products yet' info message."""
    assert len(tracked_products_page.info) > 0
    assert any("No tracked products yet." in elem.value for elem in tracked_products_page.info)
