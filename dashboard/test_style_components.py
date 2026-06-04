"""Tests for style_components.py."""

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def app_test():
    """Fixture to create and run AppTest for style_components."""
    at = AppTest.from_file("app_test_helper.py")
    at.run()
    return at


def test_render_header_layout(app_test):
    """Tests that render_header creates the correct column layout."""
    assert len(app_test.columns) >= 3

def test_render_header_displays_content(app_test):
    """Tests that render_header displays all expected text elements."""
    header_text = " ".join([h.value for h in app_test.header])
    assert "Hardware Hound" in header_text
    assert "Menu" in header_text
    assert "User" in header_text
