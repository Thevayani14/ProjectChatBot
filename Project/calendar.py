import streamlit as st
from streamlit_calendar import calendar
from database import get_calendar_events, save_calendar_events, delete_calendar_event

def calendar_page():
    """
    Displays a full-screen, interactive calendar for viewing, adding, and deleting events.
    """
    st.set_page_config(layout="wide") # Use the full width of the page

    st.title("📅 My Calendar & Notes")
    
    # Navigation button to go back to the main dashboard
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = "homepage"
        # Reset the layout to centered for the homepage
        st.set_page_config(layout="centered")
        st.rerun()

    st.markdown("---")

    # --- TWO-COLUMN LAYOUT FOR CALENDAR AND MANAGEMENT PANEL ---
    left_col, right_col = st.columns([0.65, 0.35]) # Calendar gets 65% of space

    with right_col:
        st.subheader("Manage Events")
        
        # Get the state back from the calendar component
        calendar_state = st.session_state.get("full_calendar", {})

        # --- Logic for Adding/Deleting Events ---
        # Case 1: An event was clicked (for deletion)
        if calendar_state.get("eventClick"):
            clicked_event = calendar_state["eventClick"]["event"]
            st.info(f"Selected Event: **{clicked_event['title']}**")
            
            if st.button(f"Delete this event", key=f"delete_full_{clicked_event['id']}", type="primary", use_container_width=True):
                event_id_to_delete = int(clicked_event['id'])
                if delete_calendar_event(event_id_to_delete):
                    st.toast("Event deleted!")
                    st.session_state.full_calendar["eventClick"] = None
                    st.rerun()
                else:
                    st.error("Failed to delete event.")

        # Case 2: A date was clicked (for adding a new note)
        elif calendar_state.get("select"):
            start_date_str = calendar_state["select"]["start"].split("T")[0]
            with st.form(key="add_event_form_full"):
                st.write(f"**Add a new note for {start_date_str}**")
                event_title = st.text_input("Note / Event Title:")
                submitted = st.form_submit_button("Add to Calendar")
                
                if submitted and event_title:
                    new_event = {
                        "title": event_title,
                        "start": start_date_str,
                        "end": start_date_str,
                        "color": "#6f42c1" # Purple for user-added notes
                    }
                    if save_calendar_events(st.session_state.user_id, [new_event], is_generated=False):
                        st.toast("Note added!")
                        st.session_state.full_calendar["select"] = None
                        st.rerun()
                    else:
                        st.error("Failed to add note.")
        else:
            st.info("Click on a day in the calendar to add a note, or click on an existing event to manage it.")
            
    with left_col:
        # Fetch all events for the current user from the database
        events = get_calendar_events(st.session_state.user_id)
        
        # Configure calendar options
        calendar_options = {
            "editable": False,
            "selectable": True,
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,listWeek"
            },
            "initialView": "dayGridMonth",
            "height": "auto" # Let the container define the height
        }
        
        # Render the calendar
        st.session_state.full_calendar = calendar(
            events=events,
            options=calendar_options,
            key="full_calendar_component"
        )
