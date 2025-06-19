import streamlit as st
import google.generativeai as genai
import json
import re
from datetime import datetime, date, timedelta
from collections import defaultdict

from database import get_latest_assessment_score, get_user_conversations, delete_conversation
from assessment import get_severity_and_feedback
from google_calendar import add_events_to_calendar, convert_ai_to_google_events

def schedule_sidebar():
    """The main sidebar shown on the schedule and assessment pages."""
    display_name = st.session_state.user_data.get('full_name') or st.session_state.user_data.get('username')
    st.sidebar.title(f"Welcome, {display_name}!")
    # ... (The rest of the sidebar logic is the same) ...

def configure_gemini():
    # ... (unchanged)

def parse_ai_response_to_events(response_text):
    # ... (unchanged)

def generate_schedule(score, severity, preferences):
    # ... (The prompt and generation logic is unchanged) ...

def schedule_generator_page():
    schedule_sidebar()
    st.title("📅 Generate Your Self-Care Schedule")
    st.markdown("Based on your assessment, let's create a supportive weekly plan and add it to your personal Google Calendar.")
    st.markdown("---")
    
    user_id = st.session_state.user_data['id']
    score = get_latest_assessment_score(user_id)
    
    if score is None:
        st.warning("You need to complete an assessment first to generate a personalized schedule.")
        if st.button("Go to Assessment"):
            st.session_state.page = "assessment"
            # (reset assessment state...)
            st.rerun()
    else:
        severity, _ = get_severity_and_feedback(score)
        st.info(f"Generating a schedule based on your latest assessment score of **{score}/27** (Severity: **{severity}**).")
        
        preferences = st.text_area("To help personalize your schedule...", placeholder="e.g., listening to music, reading...")
        
        if st.button("Generate & Add to My Google Calendar", use_container_width=True, type="primary"):
            if not preferences:
                st.error("Please enter at least one preference.")
            else:
                ai_response_text = generate_schedule(score, severity, preferences)
                ai_events = parse_ai_response_to_events(ai_response_text)
                
                if ai_events:
                    google_events_to_add = convert_ai_to_google_events(ai_events)
                    
                    with st.spinner("Adding events to your Google Calendar..."):
                        success_count = add_events_to_calendar(google_events_to_add)

                    if success_count > 0:
                        st.success(f"Successfully added {success_count} new events to your personal Google Calendar!")
                        st.info("You can view your updated calendar on the Dashboard.")
                        st.balloons()
                    else:
                        st.error("Could not add events to your Google Calendar. Please check permissions or try again.")
