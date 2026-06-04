"""Tests for the tracked products page."""
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

_MOCK_PRODUCT = {
    "product_name": "Test GPU",
    "product_url": "https://ebuyer.com/product",
    "site": "ebuyer",
    "currency": "GBP",
    "target_price": 69999,
    "original_price": 74999,
    "current_price": 72000,
}


def test_render_tracked_products_shows_product_cards():
    """render_tracked_products should display a card for each tracked product."""
    with patch("database.get_tracked_products", return_value=[_MOCK_PRODUCT]):
        at = AppTest.from_file("tracked_products.py")
        at.session_state["user"] = {"id": 1}
        at.run()

    assert not at.exception
    assert "Your Tracked Products" in at.title[0].value
    assert any("Test GPU" in m.value for m in at.markdown)


def test_render_tracked_products_shows_empty_state():
    """render_tracked_products should show an info message when there are no tracked products."""
    with patch("database.get_tracked_products", return_value=[]):
        at = AppTest.from_file("tracked_products.py")
        at.session_state["user"] = {"id": 1}
        at.run()

    assert not at.exception
    assert len(at.info) == 1
    assert "not tracking any products" in at.info[0].value


def test_render_tracked_products_shows_error_on_db_failure():
    """render_tracked_products should show an error message when the DB call fails."""
    with patch("database.get_tracked_products", side_effect=Exception("DB error")):
        at = AppTest.from_file("tracked_products.py")
        at.session_state["user"] = {"id": 1}
        at.run()

    assert not at.exception
    assert len(at.error) == 1
    assert "Could not load" in at.error[0].value
