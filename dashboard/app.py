# pylint: disable=broad-exception-caught
"""Hardware Hound – Streamlit dashboard application."""
import logging
import os

import streamlit as st

from auth import login_user, register_user, verify_email_token
from ses_email import send_verification_email
from form import form_page
from database import get_tracked_products
from tracked_products import render_tracked_products
from style_components import (
    add_image,
    render_header
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Hardware Hound",
    page_icon="🐾",
    layout="centered"
)

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS = {
    "user": None,
    "page": "login",
    "flash_success": None,
    "flash_error": None,
}
for _key, _val in _DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _val


# ── Handle email-verification query param ────────────────────────────────────
# Runs once per browser session when the user arrives via a verification link.
if "verify_token" in st.query_params and "token_processed" not in st.session_state:
    _token = st.query_params["verify_token"]
    st.session_state["token_processed"] = True
    logger.info("Email verification token received via query param")
    try:
        if verify_email_token(_token):
            logger.info("Email verification succeeded")
            st.session_state["flash_success"] = (
                "Your email has been verified! You can now log in."
            )
        else:
            logger.warning("Email verification failed (invalid/expired token)")
            st.session_state["flash_error"] = (
                "Verification link is invalid or has expired. Please register again."
            )
    except Exception as e:
        logger.error("Unexpected error during email verification: %s", e)
        st.session_state["flash_error"] = (
            "Could not process your verification link. Please try again later."
        )
    del st.query_params["verify_token"]


# ── Helpers ───────────────────────────────────────────────────────────────────
def _go(page: str) -> None:
    st.session_state.page = page
    st.rerun()


def _show_flash() -> None:
    if st.session_state.flash_success:
        st.success(st.session_state.flash_success)
        st.session_state.flash_success = None
    if st.session_state.flash_error:
        st.error(st.session_state.flash_error)
        st.session_state.flash_error = None


# ── Page: Login ───────────────────────────────────────────────────────────────
def render_login() -> None:
    """Render the login page."""
    add_image("hardware_hound_logo_cropped.png", width=150)
    st.title(":orange[Hardware Hound]")

    st.subheader("Log in to your account")
    _show_flash()

    with st.form("login_form"):
        email = st.text_input("Email address")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", use_container_width=True)

    if submitted:
        if not email or not password:
            st.error("Please enter your email and password.")
        else:
            try:
                user = login_user(email.strip().lower(), password)
                if user is None:
                    st.error("Incorrect email or password.")
                else:
                    logger.info(
                        "User logged in via UI: user_id=%s", user["id"])
                    st.session_state.user = user
                    _go("home")
            except ValueError as e:
                logger.warning("Login blocked for %s: %s", email, e)
                st.warning(str(e))
            except Exception as e:
                logger.error("Unhandled error on login for %s: %s", email, e)
                st.error(
                    "Unable to connect to the database. Please try again later.")

    st.divider()
    if st.button("Don't have an account? Sign up", use_container_width=True):
        _go("register")


# ── Page: Register ────────────────────────────────────────────────────────────
def render_register() -> None:
    """Render the registration page."""
    add_image("hardware_hound_logo_cropped.png", width=150)
    st.title(":orange[Hardware Hound]")

    st.subheader("Create a new account")
    _show_flash()

    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email address")
        password = st.text_input(
            "Password", type="password", help="Must be at least 8 characters."
        )
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button(
            "Create account", use_container_width=True)

    if submitted:
        if not all([username, email, password, confirm]):
            st.error("Please fill in all fields.")
        elif password != confirm:
            st.error("Passwords do not match.")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters long.")
        else:
            try:
                result = register_user(
                    username.strip(), email.strip().lower(), password
                )
                base_url = os.getenv("APP_BASE_URL", "http://localhost:8501")
                email_sent = send_verification_email(
                    to_email=email.strip().lower(),
                    username=username.strip(),
                    verification_token=result["verification_token"],
                    base_url=base_url,
                )
                if not email_sent:
                    logger.error(
                        "Verification email failed to send for user_id=%s", result["user_id"])
                else:
                    logger.info(
                        "Verification email sent to %s (user_id=%s)", email, result["user_id"])
                st.session_state.flash_success = (
                    f"Account created! A verification link has been sent to "
                    f"**{email.strip().lower()}**. "
                    "Please verify your email before logging in."
                )
                _go("login")
            except ValueError as e:
                logger.warning("Registration rejected for %s: %s", email, e)
                st.error(str(e))
            except Exception as e:
                logger.error(
                    "Unhandled error during registration for %s: %s", email, e)
                st.error("Could not create your account. Please try again later.")

    st.divider()
    if st.button("Already have an account? Log in", use_container_width=True):
        _go("login")


# ── Page: Home (authenticated) (placeholder) ────────────────────────────────────────────────
def render_home() -> None:
    """Render the home page for authenticated users."""
    user = st.session_state.user

    render_header()
    st.write(f"Welcome back, **{user['username']}**!")
    st.divider()

    try:
        tracked_count = len(get_tracked_products(user["id"]))
    except Exception:
        tracked_count = 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tracked products", tracked_count)
    with col2:
        st.metric("Active price alerts", 0)


# ── Sidebar ────────────────────────────────────────────────────────────────────
def render_sidebar() -> None:
    """Render the sidebar with navigation options for all authenticated pages."""
    user = st.session_state.user

    with st.sidebar:
        st.markdown(f"**{user['username']}**")
        st.caption(user["email"])
        st.divider()

        if st.button("Home", use_container_width=True):
            _go("home")
        if st.button("Add Product", use_container_width=True):
            _go("add_product")
        if st.button("Tracked Products", use_container_width=True):
            _go("tracked_products")

        st.divider()
        if st.button("Log out", use_container_width=True):
            logger.info("User logged out: user_id=%s", user["id"])
            st.session_state.user = None
            st.session_state.page = "login"
            st.session_state.pop("token_processed", None)
            st.rerun()


# ── Router ────────────────────────────────────────────────────────────────────
if st.session_state.user:
    render_sidebar()
    if st.session_state.page == "add_product":
        form_page()
    elif st.session_state.page == "tracked_products":
        render_tracked_products()
    else:
        render_home()
elif st.session_state.page == "register":
    render_register()
else:
    render_login()
