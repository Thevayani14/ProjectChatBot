# pages/1_🏠_Homepage.py

import streamlit as st
from collections import defaultdict
from datetime import datetime, date

# Local imports from the root directory
from database import get_google_calendar_id

# --- PAGE GUARD ---
# This ensures that a user must be logged in to see this page.
if not st.session_state.get("logged_in"):
    st.error("Please log in to access this page.")
    st.stop() # Stop the page from rendering further

# --- PAGE CONTENT ---
display_name = st.session_state.user_data.get('full_name') or st.session_state.user_data.get('username')

# THIS IS THE CORRECTED TITLE LINE
st.title(f"Dashboard for {display_name}")

st.markdown("Select an action or view your personal calendar.")
st.markdown("---")

# --- TWO-COLUMN LAYOUT for the main content ---
left_col, right_col = st.columns([0.55, 0.45])

# --- LEFT COLUMN: ACTION CARDS ---
with left_col:
    st.subheader("Get Started")
    
    # Action Card for Assessment
    with st.container(border=True):
        st.markdown("#### 🧠 Mental Health Assessment")
        st.markdown("Take the PHQ-9 screening to check in with your emotional well-being.")
        # Use st.page_link for multipage app navigation
        st.page_link("pages/2_🧠_Assessment.py", label="Start New Assessment", use_container_width=True)

    # Action Card for Schedule Generation
    with st.container(border=True):
        st.markdown("#### ✍️ Generate Self-Care Schedule")
        st.markdown("Get a personalized weekly plan added directly to your Google Calendar.")
        st.page_link("pages/3_✍️_Schedule_Generator.py", label="Generate/Update Schedule", use_container_width=True)

# --- RIGHT COLUMN: CALENDAR PREVIEW ---
with right_col:
    st.subheader("Your Personal Calendar")
    
    user_data = st.session_state.user_data
    calendar_id_to_display = None
    is_google_user = False

    # Determine which calendar to show based on user type
    if user_data.get('refresh_token'):
        # This is a Google OAuth user, show their primary calendar
        calendar_id_to_display = user_data['email']
        is_google_user = True
    elif user_data.get('google_calendar_id'):
        # This is a password-based user, show their app-managed calendar
        calendar_id_to_display = user_data.get('google_calendar_id')

    if calendar_id_to_display:
        with st.container(border=True):
            st.components.v1.iframe(
                f"https://calendar.google.com/calendar/embed?src={calendar_id_to_display}&ctz=UTC&mode=WEEK",
                height=500,
                scrolling=True
            )
            # Provide a direct link for easier editing
            if is_google_user:
                st.link_button("Open My Google Calendar ↗️", "https://calendar.google.com/", use_container_width=True)
            else:
                st.link_button("Open My App Calendar ↗️", f"https://calendar.google.com/calendar/u/0?cid={calendar_id_to_display}", use_container_width=True)
    else:
        st.warning("Your personal calendar is not set up yet. Try generating a schedule or re-logging.")
