"""Script which builds a tracked products page for a Streamlit dashboard."""

import streamlit as st


def render_tracked_products() -> None:
    """Render the tracked products page for authenticated users."""
    st.title("Your Tracked Products")
    st.markdown("Products you are currently tracking:")
    # add functionality to display tracked products here
    st.info("No tracked products yet.")


if __name__ == "__main__":
    render_tracked_products()
