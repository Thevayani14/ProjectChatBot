import streamlit as st
from login import login_page
from homepage import homepage
from assessment import assessment_page
from schedule_generator import schedule_generator_page
from calendar_page import calendar_page # <-- IMPORT THE NEW PAGE

def main():
    # st.set_page_config is now handled by each page to set layout
    # This prevents errors from calling it multiple times.

    if "page" not in st.session_state:
        st.session_state.page = "login"

    # --- Main App Flow Router ---
    if st.session_state.page == "login":
        st.set_page_config(layout="centered")
        login_page()
    elif st.session_state.page == "homepage":
        st.set_page_config(layout="centered")
        homepage()
    elif st.session_state.page == "assessment":
        st.set_page_config(layout="centered")
        assessment_page()
    elif st.session_state.page == "schedule_generator":
        st.set_page_config(layout="centered")
        schedule_generator_page()
    elif st.session_state.page == "calendar": # <-- ADD THE NEW ROUTE
        # The calendar page sets its own wide layout
        calendar_page()

if __name__ == "__main__":
    main()
