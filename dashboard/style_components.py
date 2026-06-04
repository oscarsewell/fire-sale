"""Script for reusable style components in the dashboard."""

import streamlit as st

# --- THEME VARIABLES ---

## Spacing for header (text, images and dividers)
SPACING_NONE = "0rem"
SPACING_SLIGHT = "0.5rem"
SPACING_ONE = "1rem"
SPACING_MAX = "2.5rem"

CONTAINER_PADDING = "20px"

# Colours
BG_LIGHT_BLUE = "#ededff" # we dont want that colour
BORDER_DARK_BLUE = "#03045e"
LABEL_OFF_WHITE = "#f9fafb"

# Sizing
BORDER_WIDTH = "2px"
BORDER_RADIUS = "10px"


def page_layout(layout: str) -> None:
    """Defines the overall page layout (narrow or wide)."""
    st.set_page_config(layout=layout)


def render_header() -> None:
    """Render the app header with logo and title."""
    left_column, center_column, right_column = st.columns([2, 1, 1])

    with left_column:
        image, product_name = st.columns([0.2, 0.7], gap=None)
        with image:
            add_image("hardware_hound_logo_cropped.png", width=120)
        with product_name:
            st.header(":orange[Hardware Hound]", width="content")
    
    with center_column:
        st.header("Menu")
    
    with right_column:
        st.header("User", text_alignment="right")
    
    st.divider()


def _apply_css(css: str) -> None:
    """Internal helper to apply CSS styles to the page."""
    st.markdown(css, unsafe_allow_html=True)


def header_spacing() -> None:
    """Defines smaller spacing for the header."""
    css = f"""
    <style>
    .block-container {{
        margin-top: {SPACING_NONE};
        margin-bottom: {SPACING_NONE};
        padding-top: {SPACING_MAX};
        padding-bottom: {SPACING_NONE};
    }}
    hr {{
        margin-top: {SPACING_NONE};
        margin-bottom: {SPACING_NONE};
    }}
    </style>
    """
    _apply_css(css)


def add_image(file_path: str, width: int = 200, caption: str = None) -> None:
    """Adds an image to the page with optional caption."""
    css = f"""
    <style>
    img {{
        margin: {SPACING_NONE};
        padding: {SPACING_NONE};
    }}
    </style>
    """

    _apply_css(css)
    st.image(file_path, width=width, caption=caption, clamp=True)


def page_title(title: str) -> None:
    """Displays the title of the page."""
    st.title(f":blue[{title}]",
             text_alignment="center")


def header_text_colour() -> None:
    """Defines the header text colour (not the brand name)."""
    css = f"""
    <style>
    .header-label {{color: {LABEL_OFF_WHITE};}}
    </style>   
    """
    _apply_css(css)
