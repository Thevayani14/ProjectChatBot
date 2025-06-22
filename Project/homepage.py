import streamlit as st
from collections import defaultdict
from datetime import datetime, date

from database import get_user_conversations, delete_conversation, get_google_calendar_id

def homepage_sidebar():
    """The main sidebar for the application."""
    display_name = st.session_state.user_data.get('full_name') or st.session_state.user_data.get('username')
    st.sidebar.title(f"Welcome, {display_name}!")
    
    if st.sidebar.button("🏠 Dashboard", use_container_width=True):
        st.session_state.page = "homepage"
        if "assessment_active" in st.session_state:
            del st.session_state.assessment_active
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Assessment History")
    
    conversations = get_user_conversations(st.session_state.user_data['id'])
    if not conversations:
        st.sidebar.write("No past assessments found.")
    else:
        grouped_convs = defaultdict(list)
        for conv in conversations:
            timestamp_str = conv.get('start_time')
            dt_object = None
            if timestamp_str:
                try:
                    ts = timestamp_str.split('+')[0].split('.')[0]
                    dt_object = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError): dt_object = None
            
            today = date.today()
            if dt_object:
                if dt_object.date() == today: friendly_date_key = "Today"
                elif dt_object.date() == date.fromordinal(today.toordinal() - 1): friendly_date_key = "Yesterday"
                else: friendly_date_key = dt_object.strftime("%B %d, %Y")
            else:
                friendly_date_key = "Unknown Date"
            grouped_convs[friendly_date_key].append(conv)
        
        for friendly_date, conv_list in grouped_convs.items():
            with st.sidebar.expander(f"**{friendly_date}**", expanded=True):
                for conv in conv_list:
                    col1, col2 = st.columns([0.85, 0.15])
                    with col1:
                        if st.button(f"📜 {conv['title']}", key=f"conv_{conv['id']}", use_container_width=True):
                            st.session_state.page = "assessment"
                            st.session_state.assessment_conversation_id = conv['id']
                            st.session_state.assessment_messages = []
                            st.session_state.assessment_active = False
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_hist_{conv['id']}", use_container_width=True, help=f"Delete '{conv['title']}'"):
                            delete_conversation(conv['id'])
                            st.toast(f"Deleted '{conv['title']}'.")
                            st.rerun()
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

def homepage():
    """The main dashboard page with action cards and Google Calendar display."""
    homepage_sidebar()
    
    display_name = st.session_state.user_data.get('full_name') or st.session_state.user_data.get('username')
    st.title(f"Dashboard for {display_name}")
    st.markdown("Select an action or view your personal calendar.")
    st.markdown("---")

    left_col, right_col = st.columns([0.55, 0.45])

    with left_col:
        st.subheader("Get Started")
        with st.container(border=True):
            st.markdown("#### 🧠 Mental Health Assessment")
            st.markdown("Take the PHQ-9 screening to check in with your emotional well-being.")
            if st.button("Start New Assessment", use_container_width=True):
                st.session_state.page = "assessment"
                st.session_state.assessment_active = True
                st.session_state.assessment_conversation_id = None
                st.session_state.assessment_messages = []
                st.session_state.answers = []
                st.session_state.current_question = 0
                st.rerun()

        with st.container(border=True):
            st.markdown("#### ✍️ Generate Self-Care Schedule")
            st.markdown("Get a personalized weekly plan added directly to your Google Calendar.")
            if st.button("Generate/Update Schedule", use_container_width=True):
                st.session_state.page = "schedule_generator"
                st.rerun()

    with right_col:
        st.subheader("Your Personal Calendar")
        
        user_data = st.session_state.user_data
        calendar_id_to_display = None
        is_google_user = False

        if user_data.get('refresh_token'):
            calendar_id_to_display = user_data['email']
            is_google_user = True
        elif user_data.get('google_calendar_id'):
            calendar_id_to_display = user_data.get('google_calendar_id')

        if calendar_id_to_display:
            with st.container(border=True):
                st.components.v1.iframe(
                    f"https://calendar.google.com/calendar/embed?src={calendar_id_to_display}&ctz=UTC&mode=WEEK",
                    height=500,
                    scrolling=True
                )
                if is_google_user:
                    st.link_button("Open My Google Calendar ↗️", "https://calendar.google.com/", use_container_width=True)
                else:
                    st.link_button("Open My App Calendar ↗️", f"https://calendar.google.com/calendar/u/0?cid={calendar_id_to_display}", use_container_width=True)
        else:
            st.warning("Your personal calendar is not set up yet. Try generating a schedule or re-logging.")
