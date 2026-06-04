"""Conftest for Dashboard tests."""

import pytest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import os

@pytest.fixture(scope="session")
def app_test():
    """Fixture to create and run AppTest for style_components, mocking the image."""
    # Patch st.image to avoid file loading issues
    with patch('streamlit.image'):
        at = AppTest.from_file("app.py", default_timeout=10)
        at.run()
    return at