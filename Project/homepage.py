import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from database import get_calendar_events, save_calendar_events, delete_calendar_event
from datetime import datetime

def homepage_sidebar():
    """
    Displays a simplified sidebar for the homepage, primarily for logging out.
    """
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        # Clear all session data to log out
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

def homepage():
    """
    The main function for the user's dashboard page.
    Displays navigation, an interactive calendar, and event management forms.
    """
    # Render the sidebar
    homepage_sidebar()
    
    # --- PAGE HEADER ---
    st.title(f"Dashboard for {st.session_state.username}")
    st.markdown("Here is your interactive calendar. Click a day to add a note, or click an event to manage it.")
    st.markdown("---")

    # --- TWO-COLUMN LAYOUT ---
    # The left column is for actions and forms, the right is for the calendar display.
    left_col, right_col = st.columns([0.4, 0.6]) # Left column is 40%, Right is 60%

    # --- LEFT COLUMN: ACTIONS AND FORMS ---
    with left_col:
        st.subheader("Actions")
        
        # Navigation buttons
        if st.button("🧠 Start New Assessment", use_container_width=True):
            st.session_state.page = "assessment"
            # Reset state for a fresh assessment
            st.session_state.assessment_active = True
            st.session_state.assessment_conversation_id = None
            st.session_state.assessment_messages = []
            st.session_state.answers = []
            st.session_state.current_question = 0
            st.rerun()

        if st.button("✍️ Update/Generate Schedule", use_container_width=True):
            st.session_state.page = "schedule_generator"
            st.rerun()
        
        st.markdown("---")
        
        # --- Interactive Event Management Panel ---
        st.subheader("Manage Calendar Events")
        
        # Get the state back from the calendar component, which is stored in the session
        calendar_state = st.session_state.get("schedule_calendar", {})

        # Case 1: An event was clicked (for deletion)
        if calendar_state.get("eventClick"):
            clicked_event = calendar_state["eventClick"]["event"]
            st.info(f"Selected Event: **{clicked_event['title']}**")
            
            # Use a unique key for the delete button to avoid conflicts
            if st.button(f"Delete this event", key=f"delete_{clicked_event['id']}", type="primary", use_container_width=True):
                event_id_to_delete = int(clicked_event['id'])
                if delete_calendar_event(event_id_to_delete):
                    st.toast("Event deleted!")
                    # Clear the eventClick state to prevent re-triggering after rerun
                    st.session_state.schedule_calendar["eventClick"] = None
                    st.rerun()
                else:
                    st.error("Failed to delete event.")

        # Case 2: A date on the calendar was clicked (for adding a new note)
        elif calendar_state.get("select"):
            start_date_str = calendar_state["select"]["start"].split("T")[0]
            with st.form(key="add_event_form"):
                st.write(f"**Add a new note for {start_date_str}**")
                event_title = st.text_input("Note / Event Title:")
                submitted = st.form_submit_button("Add to Calendar")
                
                if submitted and event_title:
                    new_event = {
                        "title": event_title,
                        "start": start_date_str, # An all-day event/note
                        "end": start_date_str,
                        "color": "#6f42c1" # A distinct purple color for user-added notes
                    }
                    if save_calendar_events(st.session_state.user_id, [new_event], is_generated=False):
                        st.toast("Note added!")
                        # Clear the select state to prevent re-triggering after rerun
                        st.session_state.schedule_calendar["select"] = None
                        st.rerun()
                    else:
                        st.error("Failed to add note.")
        else:
            # Default instruction text when nothing is selected
            st.info("Click on a day in the calendar to add a note, or click on an existing event to manage it.")

    # --- RIGHT COLUMN: CALENDAR DISPLAY ---
    with right_col:
        # Inject custom CSS to control the calendar's height
        st.markdown("""
            <style>
            .fc-view-harness {
                height: 550px !important; 
            }
            </style>
        """, unsafe_allow_html=True)

        # Fetch all events for the current user from the database
        events = get_calendar_events(st.session_state.user_id)
        
        # Configure calendar options
        calendar_options = {
            "editable": False, # Editing by dragging is complex; we use the form instead
            "selectable": True, # Crucial for allowing users to click on a day to add notes
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,listWeek"
            },
            "initialView": "dayGridMonth",
        }
        
        # Render the calendar. Its state (e.g., clicks) is saved to the session state variable
        # so the left column can react to it.
        st.session_state.schedule_calendar = calendar(
            events=events,
            options=calendar_options,
            key="schedule_calendar_component"
        )
