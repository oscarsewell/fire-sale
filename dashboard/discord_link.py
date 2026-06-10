"""Discord account linking page."""

import streamlit as st
from database import generate_discord_link_code
from style_components import (
    render_page_header,
    blue_button_style,
    header_spacing,
    page_title
)


def render_discord_link_page():
    """Render page for generating a Discord linking code."""
    render_page_header()
    header_spacing()
    user = st.session_state.user
    page_title("Connect Discord")
    st.markdown(
        "Generate a temporary code, then use it in Discord with "
        "`/link <code>` to connect your account.",
        text_alignment="center"
    )

    if user.get("discord"):
        st.success("Your Discord account is already connected.")
        st.write(f"Discord ID: `{user['discord']}`")
        return

    blue_button_style("discord_link")
    with st.container(key="discord_link"):
        if st.button("Generate Discord link code", width="stretch"):
            try:
                link_code = generate_discord_link_code(user["id"])
            except Exception:
                st.error("Could not generate a Discord link code. Please try again later.")
                return

            st.success("Discord link code generated!")
            st.code(link_code["code"])
    
            st.info(
                "This code expires in 15 minutes. "
                "Go to Discord and run `/link <code>` using this code."
            )
