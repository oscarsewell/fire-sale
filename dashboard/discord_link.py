"""Discord account linking page."""

import streamlit as st
from database import generate_discord_link_code


def render_discord_link_page():
    """Render page for generating a Discord linking code."""
    user = st.session_state.user

    st.title("Connect Discord")
    st.write(
        "Generate a temporary code, then use it in Discord with "
        "`/link <code>` to connect your account."
    )

    if user.get("discord"):
        st.success("Your Discord account is already connected.")
        st.write(f"Discord ID: `{user['discord']}`")
        return

    if st.button("Generate Discord link code", use_container_width=True):
        link_code = generate_discord_link_code(user["id"])

        st.success("Discord link code generated!")
        st.code(link_code["code"])

        st.info(
            "This code expires in 15 minutes. "
            "Go to Discord and run `/link code:` followed by this code."
        )
