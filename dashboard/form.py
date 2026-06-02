"""Script which builds a Streamlit dashboard with a submission form page."""

import streamlit as st

# This could be on a script for styling, can be called here
def page_title(title: str):
    """Displays the title of the page."""
    st.title(title, text_alignment="center")


def url_input_field() -> str:
    """Creates a text input field for the product URL."""
    return st.text_input(
        label="Product URL", 
        placeholder="https://website.com/product"
    )


def discount_input_field() -> int:
    """Creates a number input field for the target discount."""
    return st.number_input(
        label="Target Discount (GBP)", 
        min_value=0, 
        step=10
    )


def submit_button() -> bool:
    """Creates a submit button for the form."""
    return st.form_submit_button("Track Product")


def submission_validation(url: str, discount: int) -> bool:
    """Validates and handles form submission."""
    if url and discount > 0:
        st.success(f"Now tracking this product at a £{discount} target discount") 
    else:
        st.error("Please enter a valid URL and discount (over £0)")


def form():
    """Builds the form for adding a new product to track."""
    st.markdown("Add a new product to track")
    
    # Input fields
    url = url_input_field()
    target_discount = discount_input_field()
    
    # Submit button
    submitted = submit_button()
    
    if submitted:
        submission_validation(url, target_discount)


def form_page():
    """Builds the complete form page of the dashboard."""
    page_title("Product Tracking Form")

    with st.form("tracking_form"):
        form()


if __name__ == "__main__":
    form_page()
