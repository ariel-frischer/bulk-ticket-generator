import os
import streamlit as st

def is_secret_key_valid(entered_key):
    return entered_key == os.environ.get("APP_ACCESS_SECRET_KEY")

def initialize_secret_key():
    if "secret_key" not in st.session_state:
        st.session_state.secret_key = ""
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False

def handle_secret_key_input():
    st.text_input(
        "Secret Key",
        type="password",
        key="secret_key_input",
        on_change=lambda: setattr(
            st.session_state, "secret_key", st.session_state.secret_key_input
        ),
    )

    if st.session_state.secret_key:
        if is_secret_key_valid(st.session_state.secret_key):
            st.session_state.is_authenticated = True
            st.success("Secret key is correct. You can now use the app.")
        else:
            st.error("Incorrect secret key. Please try again.")
            st.session_state.is_authenticated = False

    if not st.session_state.is_authenticated:
        st.warning(
            "Please enter the correct secret key to use the app. All functionality is disabled until then."
        )
