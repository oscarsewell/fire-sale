"""Conftest for Dashboard tests."""

import pytest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

@pytest.fixture(scope="session")
def app_test():
    """Fixture to create and run AppTest for style_components, mocking the image."""
    with patch('streamlit.image'):
        at = AppTest.from_file("app.py", default_timeout=10)
        at.run()
    return at
