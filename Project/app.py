import streamlit as st
from login import login_page
from main_app import main_app

def main():
    """The single entry point for the entire application."""
    st.set_page_config(page_title="Mental Health Companion")

    # Initialize session state for login status
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # --- The Great Gatekeeper ---
    if st.session_state.logged_in:
        # If logged in, show the main application.
        main_app()
    else:
        # If not logged in, show the login page.
        login_page()

if __name__ == "__main__":
    main()
