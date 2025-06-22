import streamlit as st
from homepage import homepage
from assessment import assessment_page
from schedule_generator import schedule_generator_page

def main_app():
    """
    This is the main application router shown AFTER a user is logged in.
    """
    # The page routing logic now lives inside the main app.
    page = st.session_state.get("page", "homepage")

    if page == "homepage":
        homepage()
    elif page == "assessment":
        assessment_page()
    elif page == "schedule_generator":
        schedule_generator_page()
    else:
        # Default to homepage if the page state is invalid
        st.session_state.page = "homepage"
        st.rerun()
