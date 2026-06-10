"""Script which builds a Streamlit dashboard with a submission form page."""

import logging
import re
import os
import importlib.util
import sys
import streamlit as st

from database import upsert_product, add_tracked_product
from style_components import (
    render_page_header,
    page_title,
    header_spacing
)

logger = logging.getLogger(__name__)


def url_input_field() -> str:
    """Creates a text input field for the product URL."""
    return st.text_input(
        label="Product URL",
        placeholder="https://website.com/product"
    )


def target_price_input_field() -> int:
    """Creates a number input field for the target price."""
    return st.number_input(
        label="Target Price (GBP)",
        min_value=0,
        step=10
    )


def submit_button() -> bool:
    """Creates a submit button for the form."""
    return st.form_submit_button("Track", type="primary", width="stretch")


def validate_submission(url: str, target_price: int) -> dict:
    """Validates the form submission and collects all errors."""
    errors = []
    domain = check_url_scrapable(url)

    if not domain:
        errors.append("Please enter a valid URL from our supported websites")
    if target_price <= 0:
        errors.append("Please enter a target price over £0")

    return {
        'is_valid': not errors,
        'errors': errors,
        'domain': domain
    }


def track_product(domain: str, url: str, target_price: int, user_id: int) -> None:
    """Tracks a product using the appropriate scraper and saves it to the DB."""
    scraper_path = get_scraper_path(domain)
    products = call_scraper(scraper_path, url)

    if not products or not products[0].get("page_exists"):
        st.error(
            "Could not retrieve product information. Please check the URL and try again.")
        return

    product = products[0]
    try:
        cleaning_path = get_cleaning_path()
        cleaning = import_cleaning_module(cleaning_path)

        cleaned_name = cleaning.clean_product_name(product["product_name"])
        cleaned_currency = cleaning.clean_currency(product["currency_code"])
        original_price = cleaning.parse_price(product["current_price"])

        product_id = upsert_product(
            url=url,
            product_name=cleaned_name,
            site=product["website_name"],
            currency=cleaned_currency,
        )
        # target_price and original_price stored in pence
        target_price = int(target_price * 100)

        add_tracked_product(user_id, product_id, target_price, original_price)
        st.success(
            f"Success! Now tracking this product at a £{target_price / 100:.2f} target price")
        display_product_info(product)
    except ValueError as e:
        st.warning(str(e))
    except Exception as e:
        logger.error("Error saving tracked product for URL %s: %s", url, e)
        st.error(f"Could not save tracked product: {e}")


def display_product_info(product: dict) -> None:
    """Displays product information in a container."""
    with st.container(border=True):
        st.subheader(":blue[Product Information]", text_alignment="center")
        for key, value in product.items():
            if key in {"scraped_at", "page_exists", "currency_code"}:
                continue

            st.markdown(
                f'<div style="background-color: #E8F8FD; padding: 15px; border-radius: 8px; margin-bottom: 10px;">'
                f'<p style="font-weight: bold; margin: 0;">{key.replace("_", " ").title()}</p>'
                f'<p style="margin: 0; color: #555;">{value}</p>'
                f'</div>',
                unsafe_allow_html=True
            )


def submission_outcome(url: str, target_price: int, user_id: int) -> None:
    """Validates and handles form submission."""
    result = validate_submission(url, target_price)
    if result['is_valid']:
        track_product(result['domain'], url, target_price, user_id)
    else:
        for error in result['errors']:
            st.error(error)


def form(user_id: int) -> None:
    """Builds the form for adding a new product to track."""
    with st.form("tracking_form"):
        st.subheader(":blue[Submission form]", text_alignment="center")
        st.markdown("")

        url = url_input_field()
        target_price = target_price_input_field()

        st.markdown("", unsafe_allow_html=True)
        st.markdown("")
        submitted = submit_button()

        if submitted:
            submission_outcome(url, target_price, user_id)


def form_page() -> None:
    """Builds the complete form page of the dashboard."""
    render_page_header()
    header_spacing()

    page_title("Add a new product to track")
    st.markdown("")
    user_id = st.session_state.user["id"]
    form(user_id)


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
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..'))
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


def get_cleaning_path() -> str:
    """Maps to the cleaning script path."""
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(project_root, "cleaning/cleaning.py")


def import_cleaning_module(cleaning_path: str):
    """Dynamically imports the cleaning module."""
    spec = importlib.util.spec_from_file_location("cleaning", cleaning_path)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load cleaning module from: {cleaning_path}")
    cleaning = importlib.util.module_from_spec(spec)
    sys.modules["cleaning"] = cleaning
    spec.loader.exec_module(cleaning)
    return cleaning


if __name__ == "__main__":
    form_page()
