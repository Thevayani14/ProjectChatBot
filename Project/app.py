import streamlit as st
from login import login_page
from homepage import homepage
from assessment import assessment_page
from schedule_generator import schedule_generator_page

def main():
    """The main function that controls page routing."""
    st.set_page_config(page_title="Mental Health Companion")

    # Initialize session state for page routing and login status
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    # --- Main App Flow Router ---
    if not st.session_state.logged_in:
        login_page()
    elif st.session_state.page == "homepage":
        homepage()
    elif st.session_state.page == "assessment":
        assessment_page()
    elif st.session_state.page == "schedule_generator":
        schedule_generator_page()
    else: # Default to login page if state is somehow invalid
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()

if __name__ == "__main__":
    main()
