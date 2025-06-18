import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from database import get_calendar_events, save_calendar_events, delete_calendar_event, get_user_conversations, delete_conversation
from datetime import datetime, date
from collections import defaultdict

def homepage_sidebar():
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    if st.sidebar.button("Logout", use_container_width=True):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

def homepage():
    # Using a simplified sidebar for the homepage itself
    homepage_sidebar()
    
    st.title(f"Dashboard for {st.session_state.username}")
    st.markdown("Here's your interactive calendar. Click a day to add a note, or click an event to delete it.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧠 Start New Assessment", use_container_width=True):
            st.session_state.page = "assessment"
            st.session_state.assessment_active = True
            st.session_state.assessment_conversation_id = None
            st.session_state.assessment_messages = []
            st.session_state.answers = []
            st.session_state.current_question = 0
            st.rerun()
    with col2:
        if st.button("✍️ Update/Generate Schedule", use_container_width=True):
            st.session_state.page = "schedule_generator"
            st.rerun()
            
    st.markdown("---")

    # --- Interactive Calendar ---
    events = get_calendar_events(st.session_state.user_id)
    
    calendar_options = {
        "editable": False,
        "selectable": True,
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listWeek"
        },
        "initialView": "dayGridMonth",
    }
    
    calendar_state = calendar(events=events, options=calendar_options, key="schedule_calendar")

    st.markdown("---")
    st.subheader("Manage Calendar Events")

    # Case 1: An event was clicked (for deletion)
    if calendar_state.get("eventClick"):
        clicked_event = calendar_state["eventClick"]["event"]
        st.info(f"Selected: **{clicked_event['title']}**")
        if st.button(f"Delete event: '{clicked_event['title']}'", type="primary"):
            if delete_calendar_event(clicked_event['id']):
                st.toast("Event deleted!")
                st.rerun()
            else:
                st.error("Failed to delete event.")

    # Case 2: A date was clicked (for adding a new note)
    if calendar_state.get("select"):
        start_date_str = calendar_state["select"]["start"].split("T")[0]
        with st.form(key="add_event_form"):
            st.write(f"Add a new note/event for **{start_date_str}**")
            event_title = st.text_input("Note/Event Title")
            submitted = st.form_submit_button("Add Event")
            if submitted and event_title:
                new_event = {
                    "title": event_title,
                    "start": start_date_str,
                    "end": start_date_str,
                    "color": "#6f42c1" # Purple for user-added notes
                }
                if save_calendar_events(st.session_state.user_id, [new_event], is_generated=False):
                    st.toast("Note added!")
                    st.rerun()
                else:
                    st.error("Failed to add note.")
