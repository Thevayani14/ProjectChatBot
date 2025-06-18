import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from database import get_latest_schedule
from datetime import datetime
import io
import re

def parse_schedule_to_events(schedule_md):
    """Parses schedule markdown into a list of events for the calendar component."""
    if not schedule_md or "---|" not in schedule_md:
        return []

    try:
        # Isolate the table part of the markdown
        table_content = schedule_md.split('---|\n')[-1]
        table_io = io.StringIO(table_content)
        df = pd.read_csv(table_io, sep='|', names=['Day', 'Morning', 'Afternoon', 'Evening']).iloc[1:]
        df = df.apply(lambda x: x.str.strip())
    except Exception:
        return []

    events = []
    today = datetime.now()
    day_map = {day: i for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])}
    
    for _, row in df.iterrows():
        day_str = row['Day']
        if day_str not in day_map:
            continue

        days_ahead = (day_map[day_str] - today.weekday() + 7) % 7
        event_date = (today + pd.Timedelta(days=days_ahead)).date()

        if pd.notna(row['Morning']) and row['Morning']:
            events.append({"title": row['Morning'], "start": f"{event_date}T09:00:00", "end": f"{event_date}T11:00:00", "color": "#fd7e14"})
        if pd.notna(row['Afternoon']) and row['Afternoon']:
            events.append({"title": row['Afternoon'], "start": f"{event_date}T14:00:00", "end": f"{event_date}T16:00:00", "color": "#20c997"})
        if pd.notna(row['Evening']) and row['Evening']:
            events.append({"title": row['Evening'], "start": f"{event_date}T20:00:00", "end": f"{event_date}T21:00:00", "color": "#0dcaf0"})

    return events

def homepage():
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    st.title(f"Dashboard for {st.session_state.username} 🗓️")
    st.markdown("Here's your hub for assessments and your personalized weekly schedule.")

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
    st.header("Your Weekly Self-Care Plan")

    schedule_md = get_latest_schedule(st.session_state.user_id)
    if not schedule_md:
        st.info("You haven't generated a schedule yet. Go to the 'Update/Generate Schedule' page to create one!")
    else:
        calendar_events = parse_schedule_to_events(schedule_md)
        calendar_options = {
            "headerToolbar": {
                "left": "today prev,next",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,listWeek"
            },
            "initialView": "dayGridMonth",
            "slotMinTime": "06:00:00",
            "slotMaxTime": "23:00:00",
        }
        
        selected_event = calendar(events=calendar_events, options=calendar_options, key="schedule_calendar")

        if selected_event and selected_event.get('event'):
            st.info(f"Selected: {selected_event['event']['title']}")
