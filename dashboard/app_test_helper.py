"""Helper app file for testing style_components."""
import streamlit as st
from PIL import Image
import io

# Create a small test image in memory
img = Image.new('RGB', (120, 120), color='red')
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)

# Patch the add_image function to use our test image
import style_components
def mock_add_image(file_path, width=200, caption=None):
    css = f"""
    <style>
    img {{
        margin: 0rem;
        padding: 0rem;
    }}
    </style>
    """
    style_components._apply_css(css)
    st.image(img_bytes, width=width, caption=caption)

style_components.add_image = mock_add_image

from style_components import render_header, header_spacing

header_spacing()
render_header()