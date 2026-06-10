"""Tests for style_components.py."""

from unittest.mock import patch, MagicMock
from style_components import render_page_header


def test_render_page_header():
    """Tests that render_page_header runs without error."""
    with patch('style_components.st') as mock_st:
        mock_st.columns.side_effect = [
            (MagicMock(), MagicMock(), MagicMock()),
            (MagicMock(), MagicMock())
        ]
        render_page_header()
