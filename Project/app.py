# app.py

import streamlit as st
from login import login_page
from homepage import homepage
from assessment import assessment_page
from schedule_generator import schedule_generator_page

def main():
    st.set_page_config(page_title="Mental Health Companion", layout="centered")

    # Initialize session state for page routing if it doesn't exist
    if "page" not in st.session_state:
        st.session_state.page = "login"

    # --- Main App Flow Router ---
    if st.session_state.page == "login":
        # login_page will set page to "homepage" on successful login
        login_page()
    elif st.session_state.page == "homepage":
        homepage()
    elif st.session_state.page == "assessment":
        assessment_page()
    elif st.session_state.page == "schedule_generator":
        schedule_generator_page()

if __name__ == "__main__":
    main()