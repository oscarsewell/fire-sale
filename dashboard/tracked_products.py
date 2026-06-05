"""Script which builds a tracked products page for a Streamlit dashboard."""

import streamlit as st
from style_components import render_header, header_spacing, metric_style
from database import get_tracked_products


def render_tracked_products() -> None:
    """Render the tracked products page for authenticated users."""
    render_header()
    header_spacing()
    metric_style()
    st.title(":blue[Your Tracked Products]", ":paw_prints:", text_alignment="center")
    user_id = st.session_state.user["id"]

    try:
        products = get_tracked_products(user_id)
    except Exception:
        st.error("Could not load your tracked products. Please try again later.")
        return

    if not products:
        st.info(
            "You are not tracking any products yet. Use the Add Product tab to get started.")
        return

    for product in products:
        with st.container(border=True):
            st.markdown(
                f"**[{product['product_name']}]({product['product_url']})**")
            col1, col2, col3 = st.columns(3)
            currency = product["currency"]
            current = product["current_price"]
            col1.metric(
                "Current Price", f"{currency} {current / 100:.2f}" if current is not None else "N/A")
            col2.metric("Target Price",
                        f"{currency} {product['target_price'] / 100:.2f}")
            col3.metric("Original Price",
                        f"{currency} {product['original_price'] / 100:.2f}")
            st.caption(f"Site: {product['site']}")
            if st.button("Untrack", key=f"untrack_{product['product_id']}"):
                try:
                    remove_tracked_product(user_id, product["product_id"])
                    st.rerun()
                except Exception:
                    st.error("Could not untrack this product. Please try again.")


if __name__ == "__main__":
    render_tracked_products()
