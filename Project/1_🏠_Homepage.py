import streamlit as st
from streamlit_calendar import calendar
from database import get_calendar_events
from sidebar import sidebar

if not st.session_state.get("logged_in"):
    st.error("Please log in to access this page.")
    st.stop()

sidebar()
display_name = st.session_state.user_data.get('full_name') or st.session_state.user_data.get('username')
st.title(f"Dashboard for {display_name}")
# ... (rest of homepage layout with action cards) ...

with right_col:
    st.subheader("Calendar Preview")
    # ... (CSS for small calendar) ...
    with st.container(border=True):
        events = get_calendar_events(st.session_state.user_data['id'])
        calendar(events=events, options={"headerToolbar": {"left": "title", "center": "", "right": "prev,next"}, "initialView": "dayGridMonth"}, key="preview")
        st.page_link("pages/4_📅_Calendar.py", label="Expand & Edit Calendar", use_container_width=True)
