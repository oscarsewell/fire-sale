"""Script which builds a tracked products page for a Streamlit dashboard."""

from datetime import datetime
import plotly.graph_objects as go
import streamlit as st
from babel.numbers import get_currency_symbol
from style_components import render_header, header_spacing, metric_style
from database import get_tracked_products, remove_tracked_product, get_price_history


def render_tracked_products() -> None:
    """Render the tracked products page for authenticated users."""
    render_header()
    header_spacing()
    metric_style()
    st.title(":blue[Your Tracked Products]",
             ":paw_prints:", text_alignment="center")
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
            symbol = get_currency_symbol(currency, locale="en")
            current = product["current_price"] if product["current_price"] is not None else product["original_price"]
            col1.metric(
                "Current Price", f"{symbol}{current / 100:.2f}" if current is not None else "N/A")
            col2.metric("Target Price",
                        f"{symbol}{product['target_price'] / 100:.2f}")
            col3.metric("Original Price",
                        f"{symbol}{product['original_price'] / 100:.2f}")
            st.caption(f"Site: {product['site']}")

            history = get_price_history(product["product_id"])

            # Formulate history points: if no scraping has run yet, use the original_price at current time
            if not history and product["original_price"] is not None:
                history = [
                    {"scraped_at": datetime.now(), "current_price": product["original_price"]}]

            if len(history) >= 1:
                dates = [row["scraped_at"] for row in history]
                prices = [row["current_price"] / 100 for row in history]
                target = product["target_price"] / 100

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=prices,
                    mode="lines+markers" if len(history) > 1 else "markers",
                    name="Price",
                    line=dict(color="#0066cc", width=2),
                    marker=dict(size=8 if len(history) ==
                                1 else 5, color="#0066cc"),
                ))
                fig.add_hline(
                    y=target,
                    line_color="#E8611A",
                    line_width=2,
                    annotation_text=f"Target {symbol}{target:.2f}",
                    annotation_position="bottom right",
                    annotation_font_color="#E8611A",
                )
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title=f"Price ({currency})",
                    showlegend=False,
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=250,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)

            if st.button("Untrack", key=f"untrack_{product['product_id']}", type="primary"):
                try:
                    remove_tracked_product(user_id, product["product_id"])
                    st.rerun()
                except Exception:
                    st.error("Could not untrack this product. Please try again.")


if __name__ == "__main__":
    render_tracked_products()
