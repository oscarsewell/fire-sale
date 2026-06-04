"""Script which builds a Streamlit dashboard with a submission form page."""

import re
import os
import importlib.util
import sys
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


def validate_submission(url: str, discount: int) -> dict:
    """Validates the form submission and collects all errors."""
    errors = []
    domain = check_url_scrapable(url)

    if not domain:
        errors.append("Please enter a valid URL from our supported websites")
    if discount <= 0:
        errors.append("Please enter a discount over £0")

    return {
        'is_valid': not errors,
        'errors': errors,
        'domain': domain
    }


def track_product(domain: str, url: str, discount: int) -> None:
    """Tracks a product using the appropriate scraper."""
    scraper_path = get_scraper_path(domain)
    products = call_scraper(scraper_path, url)

    if products:
        st.success(f"Success! Now tracking this product at a £{discount} target discount")
        display_product_info(products[0], domain) # The scraper returns a list of products


def display_product_info(product: dict, domain: str) -> None:
    """Displays product information in a container."""
    st.subheader("Product Information")
    with st.container(border=True):
        st.markdown(f"**Product Name:** {product.get('product_name', 'N/A')}")
        st.markdown(f"**Current Price:** {product.get('current_price', 'N/A')}")
        st.markdown(f"**Website:** {domain.lower()}")


def submission_outcome(url: str, discount: int) -> None:
    """Validates and handles form submission."""
    result = validate_submission(url, discount)
    if result['is_valid']:
        track_product(result['domain'], url, discount)
    else:
        for error in result['errors']:
            st.error(error)


def form():
    """Builds the form for adding a new product to track."""
    st.markdown("Add a new product to track")

    # Input fields
    url = url_input_field()
    target_discount = discount_input_field()

    # Submit button
    submitted = submit_button()

    if submitted:
        submission_outcome(url, target_discount)


def form_page():
    """Builds the complete form page of the dashboard."""
    page_title("Product Tracking Form")

    with st.form("tracking_form"):
        form()


def is_valid_url(url: str) -> bool:
    """Checks if the product URL is valid."""
    if not url:
        return False

    url_pattern = re.compile(
        r'^(https?://)?'  # optional http or https scheme
        r'(www\.)?'
        r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # domain name
        r'(/[\w\-./?%&#=]*)?$'  # optional path and query string
    )
    return bool(url_pattern.match(url))


def extract_website_name(url: str) -> str:
    """Extracts the website name from a valid URL."""
    match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+)\.', url)
    if match:
        return match.group(1).lower()


def is_website_supported(domain: str) -> str:
    """Checks if the website name is found in the list of supported websites."""
    supported_websites = ['awd-it', 'ebuyer', 'overclockers']
    return domain in supported_websites


def check_url_scrapable(url: str) -> str:
    """Checks if the URL is valid and belongs to a supported website."""
    if not is_valid_url(url):
        return None
    domain = extract_website_name(url)
    return domain if domain and is_website_supported(domain) else None


def get_scraper_path(domain: str) -> str:
    """Maps the domain name to the corresponding scraper script path."""
    domain_normalised = domain.replace("-", "_")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(project_root, f"full_scraping/{domain}/{domain_normalised}_full_scraper.py")


def import_scraper_module(scraper_path: str):
    """Dynamically imports a scraper module."""
    spec = importlib.util.spec_from_file_location("scraper", scraper_path)
    scraper = importlib.util.module_from_spec(spec)
    sys.modules["scraper"] = scraper
    spec.loader.exec_module(scraper)
    return scraper


def call_scraper(scraper_path: str, url: str):
    """Calls the scraper function."""
    scraper = import_scraper_module(scraper_path)
    return scraper.scrape_all_products([url])


if __name__ == "__main__":
    form_page()
