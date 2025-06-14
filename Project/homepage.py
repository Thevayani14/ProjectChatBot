# homepage.py

import streamlit as st
from sidebar import show_sidebar

def homepage():

    show_sidebar()

    st.title("Welcome to Your Mental Health Companion")
    st.markdown("Please choose an option below to get started.")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div style="cursor: pointer; padding: 20px; text-align: center; border: 1px solid #ddd; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <img src="https://img.icons8.com/plasticine/100/test-tube.png" alt="Assessment Icon" width="80">
                <h3 style="margin-top: 15px;">Start Assessment</h3>
                <p>Take the PHQ-9 depression screening to check in with yourself.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Start a New Assessment", key="assessment_button", use_container_width=True):
            # Reset relevant states for a NEW assessment
            st.session_state.page = "assessment"
            st.session_state.assessment_active = True
            st.session_state.assessment_conversation_id = None
            st.session_state.assessment_messages = []
            st.session_state.answers = []
            st.session_state.current_question = 0
            st.rerun()

    with col2:
        st.markdown(
            """
            <div style="cursor: pointer; padding: 20px; text-align: center; border: 1px solid #ddd; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <img src="https://img.icons8.com/plasticine/100/calendar.png" alt="Schedule Icon" width="80">
                <h3 style="margin-top: 15px;">Generate Schedule</h3>
                <p>Get a personalized self-care schedule based on your assessment results.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Go to Schedule Generator", key="schedule_button", use_container_width=True):
            st.session_state.page = "schedule_generator"
            st.rerun()
