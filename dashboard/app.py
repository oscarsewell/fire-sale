"""Fire Sale dashboard — main entry point.

Flow:
  1. If ?verify=TOKEN is in the URL, handle email verification first.
  2. If the user is not authenticated, show the Login / Register / Resend tabs.
  3. If authenticated, show the main dashboard (tracked products).
"""
import os

import streamlit as st

import auth
import db

APP_URL = os.getenv("APP_URL", "http://localhost:8501")

st.set_page_config(
    page_title="Fire Sale",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# 1. Handle email verification via query parameter
# ---------------------------------------------------------------------------

params = st.query_params
if "verify" in params:
    token = params["verify"]
    st.query_params.clear()
    ok, msg = auth.verify_email(token)
    if ok:
        st.success(f"✅ {msg}")
    else:
        st.error(f"❌ {msg}")


# ---------------------------------------------------------------------------
# 2. Auth gate
# ---------------------------------------------------------------------------

def _show_login_tab():
    st.subheader("Log in")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Log in", use_container_width=True, key="btn_login"):
        if not email or not password:
            st.warning("Please fill in both fields.")
            return

        ok, msg = auth.login_user(email, password)
        if ok:
            st.success(msg)
            st.rerun()
        elif msg == "EMAIL_NOT_VERIFIED":
            st.warning(
                "Your email address hasn't been verified yet. "
                "Check your inbox, or use the **Resend verification** tab."
            )
        else:
            st.error(msg)


def _show_register_tab():
    st.subheader("Create an account")
    username = st.text_input("Username", key="reg_username")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Password", type="password", key="reg_password")
    confirm = st.text_input(
        "Confirm password", type="password", key="reg_confirm")

    st.caption(
        "Password must be at least 8 characters and include an uppercase letter, "
        "a lowercase letter, a number, and a special character."
    )

    if st.button("Register", use_container_width=True, key="btn_register"):
        err = auth.validate_registration(username, email, password, confirm)
        if err:
            st.error(err)
            return

        ok, msg = auth.register_user(username, email, password, APP_URL)
        if ok:
            st.success(msg)
        else:
            st.error(msg)


def _show_resend_tab():
    st.subheader("Resend verification email")
    st.write(
        "If you didn't receive your verification email, or if the link has expired, "
        "enter your address below and we'll send a fresh one."
    )
    email = st.text_input("Email", key="resend_email")

    if st.button("Resend", use_container_width=True, key="btn_resend"):
        if not email:
            st.warning("Please enter your email address.")
            return
        ok, msg = auth.resend_verification(email, APP_URL)
        if ok:
            st.success(msg)
        else:
            st.error(msg)


def _show_auth_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔥 Fire Sale")
        st.caption("Track prices across AWD-IT, Ebuyer, and Overclockers.")
        st.divider()

        tab_login, tab_register, tab_resend = st.tabs(
            ["Log in", "Register", "Resend verification"]
        )
        with tab_login:
            _show_login_tab()
        with tab_register:
            _show_register_tab()
        with tab_resend:
            _show_resend_tab()


# ---------------------------------------------------------------------------
# 3. Main dashboard (authenticated users only)
# ---------------------------------------------------------------------------

def _show_dashboard():
    user = auth.get_current_user()
    user_id = user["user_id"]

    # Sidebar
    with st.sidebar:
        st.markdown(f"**{user['username']}**")
        st.caption(user["email"])
        if user.get("discord"):
            st.caption(f"Discord: {user['discord']}")
        st.divider()
        if st.button("Log out"):
            auth.logout()
            st.rerun()

    st.title("🔥 Fire Sale — My Tracked Products")

    # Fetch tracked products
    try:
        products = db.get_tracked_products_for_user(user_id)
    except Exception as exc:
        st.error(f"Could not load your products: {exc}")
        return

    if not products:
        st.info(
            "You aren't tracking any products yet. "
            "Products are added via the scraper configuration."
        )
        return

    # Summary metrics
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Products tracked", len(products))
    below_target = sum(
        1 for p in products
        if p["latest_price"] is not None and p["latest_price"] <= p["target_price"]
    )
    col_b.metric("Below target price", below_target)
    unavailable = sum(1 for p in products if not p["page_exists"])
    col_c.metric("Unavailable listings", unavailable)

    st.divider()

    # Product cards
    for product in products:
        with st.expander(
            f"**{product['product_name']}** — {product['site_name']}",
            expanded=False,
        ):
            pcol1, pcol2 = st.columns(2)
            currency = product["currency"]

            with pcol1:
                st.markdown(f"[View listing]({product['product_url']})")
                if not product["page_exists"]:
                    st.warning("⚠️ This listing is no longer available.")

            with pcol2:
                latest = product["latest_price"]
                target = product["target_price"]
                original = product["original_price"]

                st.metric(
                    "Latest price",
                    f"{currency} {latest / 100:.2f}" if latest else "N/A",
                    delta=(
                        f"{(latest - original) / 100:.2f}" if latest else None
                    ),
                    delta_color="inverse",
                )
                st.caption(f"Original: {currency} {original / 100:.2f}")
                st.caption(f"Your target: {currency} {target / 100:.2f}")

                if latest is not None and latest <= target:
                    st.success("✅ Below your target price!")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if not auth.is_authenticated():
    _show_auth_page()
else:
    _show_dashboard()
