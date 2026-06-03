"""Script which builds a tracked products page for a Streamlit dashboard."""

import streamlit as st


def render_tracked_products() -> None:
    """Render the tracked products page for authenticated users."""
    st.title("Your Tracked Products")
    st.write("Products you are currently tracking:")
    st.info("No tracked products yet.")
