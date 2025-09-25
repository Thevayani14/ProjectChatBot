import streamlit as st
from streamlit_calendar import calendar
from database import (
    get_calendar_events, 
    save_calendar_events, 
    delete_calendar_event, 
    update_calendar_event, 
    clear_all_events, 
    update_calendar_event_completion,
    get_events_for_last_week 
)
from datetime import datetime, time, timedelta
import random
import google.generativeai as genai 
from sidebar import display_sidebar

# --- PAGE GUARD & CONFIG ---
st.set_page_config(page_title="Full Calendar", layout="wide")
if not st.session_state.get("logged_in"):
    st.error("Please log in to access this page.")
    st.switch_page("app.py")
    st.stop()

# --- HELPER FUNCTION for the AI Review ---
def configure_gemini():
    try:
        genai.configure(api_key=st.secrets.api_keys.google)
        return genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")
        return None

# --- NEW: SIDEBAR with Integrated Weekly Review ---
def display_calendar_sidebar():
    with st.sidebar:
        st.title("Calendar Tools")
        st.divider()

        with st.expander("✨ Get Your Weekly Review", expanded=True):
            if st.button("Generate My Review", use_container_width=True):
                user_id = st.session_state.user_data['id']
                last_week_events = get_events_for_last_week(user_id)

                if not last_week_events:
                    st.info("You haven't logged any activities in the past week. Complete some events to get a review!")
                else:
                    with st.spinner("AI is analyzing your week..."):
                        completed_good = [title for title, completed, mood in last_week_events if completed and mood == 1]
                        completed_ok = [title for title, completed, mood in last_week_events if completed and mood == 0]
                        completed_bad = [title for title, completed, mood in last_week_events if completed and mood == -1]
                        skipped = [title for title, completed, mood in last_week_events if not completed]

                        prompt = f"""
                        Analyze the user's activity log for the past 7 days to provide a supportive weekly review.
                        - Activities completed that felt good: {completed_good or 'None'}
                        - Activities completed that felt okay/neutral: {completed_ok or 'None'}
                        - Activities completed that felt bad: {completed_bad or 'None'}
                        - Skipped activities: {skipped or 'None'}
                        
                        Based on this, provide a short (2-3 paragraphs), encouraging summary. Highlight patterns and suggest a positive theme for the upcoming week. Keep the tone friendly and supportive.
                        """
                        model = configure_gemini()
                        if model:
                            response = model.generate_content(prompt).text
                            st.session_state.weekly_review_content = response
                        else:
                            st.error("Could not generate review.")     
        st.divider()

# --- MAIN PAGE LOGIC ---
display_sidebar() 
# --- Logic for Forcing a Refresh after generation/updates ---
force_refresh_key_suffix = ""
if st.session_state.get("calendar_force_refresh"):
    force_refresh_key_suffix = str(random.randint(1000, 9999))
    del st.session_state["calendar_force_refresh"]

# --- Initialize session state for this page ---
# Initialize session state
if 'editing_event_id' not in st.session_state: st.session_state.editing_event_id = None
if 'confirming_clear_all' not in st.session_state: st.session_state.confirming_clear_all = False
if 'logging_mood_for' not in st.session_state: st.session_state.logging_mood_for = None

st.title("My Calendar & Notes")
st.markdown("View your AI-generated schedule and manage your personal events. Mark events as 'Complete' to track your progress!")

# --- NEW: Display the Weekly Review if it was generated ---
if 'weekly_review_content' in st.session_state:
    with st.container(border=True):
        st.subheader("✨ Your Weekly Review")
        st.markdown(st.session_state.weekly_review_content)
        if st.button("Dismiss Review"):
            del st.session_state.weekly_review_content
            st.rerun()
    st.divider()

# --- CALENDAR DISPLAY ---
st.header("Calendar View")
events = get_calendar_events(st.session_state.user_data['id'])
calendar_options = {
    "headerToolbar": {"left": "today prev,next", "center": "title", "right": "dayGridMonth,timeGridWeek,listWeek"},
    "initialView": "timeGridWeek", "height": "600px","timeZone": "UTC"
}
calendar(events=events, options=calendar_options, key=f"main_calendar_{len(events)}_{force_refresh_key_suffix}")
st.divider()

# --- EVENT MANAGEMENT SECTION ---
st.header("Manage Your Events")

with st.expander("➕ Add a New Event or Note"):
    with st.form("add_form", clear_on_submit=True):
        # This form logic is correct and unchanged
        add_title = st.text_input("Event Title*")
        add_date = st.date_input("Date*")
        col1, col2 = st.columns(2)
        add_start_time = col1.time_input("Start Time (optional)", value=None)
        add_end_time = col2.time_input("End Time (optional)", value=None)
        if st.form_submit_button("Save New Event"):
            if add_title and add_date:
                final_start_time = add_start_time if add_start_time is not None else time(0, 0)
                if add_end_time is None:
                    final_end_time = (datetime.combine(add_date, final_start_time) + timedelta(hours=1)).time()
                else:
                    final_end_time = add_end_time
                if final_start_time >= final_end_time:
                    st.error("End time must be after start time.")
                else:
                    new_event = {
                        "title": add_title, "start": f"{add_date}T{final_start_time}",
                        "end": f"{add_date}T{final_end_time}", "color": "#6f42c1"
                    }
                    if save_calendar_events(st.session_state.user_data['id'], [new_event], is_generated=False):
                        st.toast("Event added successfully!")
                        st.session_state.calendar_force_refresh = True
                        st.rerun()

# --- NEW: Interactive Event List with Completion and Mood Logging ---
st.subheader("Your Current Events")
if not events:
    st.info("You have no events scheduled. Generate a schedule or add an event to get started!")
else:
    sorted_events = sorted(events, key=lambda x: x['start'])
    for event in sorted_events:
        event_id = int(event['id'])
        is_completed = event.get('completed', False)
        
        with st.container(border=True):
            col_info, col_status = st.columns([0.8, 0.2])

            # Display event info with a status icon
            with col_info:
                status_icon = "✅" if is_completed else "☑️"
                event_date_obj = datetime.fromisoformat(event['start'])
                event_date_str = event_date_obj.strftime("%a, %b %d")
                event_time_str = f" at {event_date_obj.strftime('%I:%M %p')}"
                st.markdown(f"**{status_icon} {event['title']}**")
                st.caption(f"{event_date_str}{event_time_str}")

            # Display "Complete" or "Undo" button
            with col_status:
                if not is_completed:
                    if st.button("Complete", key=f"complete_{event_id}", use_container_width=True):
                        st.session_state.logging_mood_for = event_id
                        st.rerun()
                else:
                    if st.button("Undo", key=f"undo_{event_id}", use_container_width=True):
                        if update_calendar_event_completion(event_id, False, None):
                            st.toast("Event marked as not complete.")
                            st.rerun()

            # Display mood logger if this event was just marked for completion
            if st.session_state.get("logging_mood_for") == event_id:
                st.write("**How did this activity make you feel?**")
                mood_cols = st.columns(3)
                mood_selected = None
                if mood_cols[0].button("😊 Good", key=f"mood_good_{event_id}", use_container_width=True): mood_selected = 1
                if mood_cols[1].button("😐 Okay", key=f"mood_ok_{event_id}", use_container_width=True): mood_selected = 0
                if mood_cols[2].button("😔 Not Great", key=f"mood_bad_{event_id}", use_container_width=True): mood_selected = -1
                
                if mood_selected is not None:
                    if update_calendar_event_completion(event_id, True, mood_selected):
                        st.toast("Great job tracking your progress!")
                        del st.session_state.logging_mood_for
                        st.rerun()
            
            # Expander for less-used actions
            with st.expander("Actions"):
                edit_col, delete_col = st.columns(2)
                if edit_col.button("Edit", key=f"edit_{event_id}", use_container_width=True):
                    st.session_state.editing_event_id = event_id
                    st.rerun()
                if delete_col.button("Delete", key=f"delete_{event_id}", type="primary", use_container_width=True):
                    if delete_calendar_event(event_id):
                        st.toast(f"Deleted '{event['title']}'!")
                        st.session_state.calendar_force_refresh = True
                        st.rerun()
            
            # --- THE INLINE EDIT FORM ---
            # This form only appears for the event whose "Edit" button was clicked
            if st.session_state.editing_event_id == event_id:
                with st.form(key=f"edit_form_{event_id}"):
                    st.write(f"Editing: *{event['title']}*")
                    
                    current_date = datetime.fromisoformat(event['start']).date()
                    current_start_time = datetime.fromisoformat(event['start']).time() if 'T' in event['start'] else None
                    current_end_time = datetime.fromisoformat(event['end']).time() if 'T' in event['end'] else None
                    
                    new_date = st.date_input("Date", value=current_date, key=f"date_edit_{event_id}")
                    new_start_time = st.time_input("Start Time", value=current_start_time, key=f"start_edit_{event_id}")
                    new_end_time = st.time_input("End Time", value=current_end_time, key=f"end_edit_{event_id}")
                    
                    save_col, cancel_col = st.columns(2)
                    with save_col:
                        if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
                            if new_start_time >= new_end_time:
                                st.error("End time must be after the start time.")
                            else:
                                if update_calendar_event(event_id, new_date, new_start_time, new_end_time):
                                    st.toast("Update saved!")
                                    st.session_state.editing_event_id = None
                                    st.session_state.calendar_force_refresh = True
                                    st.rerun()
                                else:
                                    st.error("Failed to save update.")
                    with cancel_col:
                        if st.form_submit_button("Cancel", use_container_width=True):
                            st.session_state.editing_event_id = None
                            st.rerun()

# --- DANGER ZONE: CLEAR ALL EVENTS ---
st.markdown("---")
st.subheader("⚠️ Danger Zone")
with st.container(border=True):
    if st.session_state.confirming_clear_all:
        st.warning("Are you sure you want to permanently delete ALL events from your calendar?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete Everything", use_container_width=True, type="primary"):
                with st.spinner("Deleting all events..."):
                    if clear_all_events(st.session_state.user_data['id']):
                        st.toast("All calendar events have been cleared.")
                        st.session_state.confirming_clear_all = False
                        st.rerun()
                    else:
                        st.error("Failed to clear events.")
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirming_clear_all = False
                st.rerun()
    else:
        st.write("This will remove all AI-generated and manually added events.")
        if st.button("Clear All Calendar Events", use_container_width=True):
            st.session_state.confirming_clear_all = True
            st.rerun()