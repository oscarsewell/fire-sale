"""Script for reusable style components in the dashboard."""

import streamlit as st

# --- THEME VARIABLES ---

## Spacing for header (text, images and dividers)
SPACING_NONE = "0rem !important"
SPACING_SLIGHT = "0.5rem"
SPACING_ONE = "1rem"
SPACING_MAX = "4rem"

CONTAINER_PADDING = "20px"

# Colours
BG_LIGHT_BLUE = "#e3efff"
BORDER_DARK_BLUE = "#03045e"
LABEL_OFF_WHITE = "#f9fafb"

# Sizing
BORDER_WIDTH = "2px"
BORDER_RADIUS = "10px"


def render_header() -> None:
    """Render the app header with logo and title."""
    left, center, right = st.columns([1, 2, 1])

    with center:
        image, product_name = st.columns([0.2, 0.7], gap=None)
        with image:
            add_image("hardware_hound_logo_cropped.png", width=120)
        with product_name:
            st.header(":orange[Hardware Hound]", width="content")
    
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
    h2 {{
        margin-top: {SPACING_NONE};
        margin-bottom: {SPACING_NONE};
        padding-top: {SPACING_NONE};
        padding-bottom: {SPACING_NONE};
    }}
    hr {{
        margin-top: {SPACING_NONE};
        margin-bottom: {SPACING_NONE};
        padding-top: {SPACING_NONE};
    }}
    </style>
    """
    _apply_css(css)


def signup_button_style() -> None:
    """Style the redirect action buttons to be centered and customized."""
    css = """
    <style>
    div.stButton {
        display: flex;
        justify-content: center;
    }
    div.stButton button {
        background-color: #0066cc;
        color: white;
        border-radius: 10px;
        padding: 10px;
        width: 95%;
    }
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


def metric_style() -> None:
    """Defines the metric label and value font sizes."""
    css = """
    <style>
    div[data-testid="stMetricValue"] {
        font-size: 2.8rem !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 3rem !important;
        font-weight: 500 !important;
    }
    </style>
    """
    _apply_css(css)


def supported_websites_container() -> None:
    """Define the supported websites container style."""
    css = """
    <style>
    .st-key-supported_websites {
        background-color: #FFEDE6;
    }
    </style>
    """
    _apply_css(css)
