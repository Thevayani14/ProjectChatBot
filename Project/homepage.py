import streamlit as st
from streamlit_calendar import calendar
from database import get_calendar_events, get_user_conversations, delete_conversation
from collections import defaultdict
from datetime import datetime, date

def homepage_sidebar():
    """
    Displays the main sidebar for the application, including user info,
    navigation, and a complete, grouped assessment history.
    """
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    
    # Navigation button for the Dashboard/Homepage
    if st.sidebar.button("🏠 Dashboard", use_container_width=True):
        st.session_state.page = "homepage"
        if "assessment_active" in st.session_state:
            del st.session_state.assessment_active
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Assessment History")

    # Fetch and display the user's past assessments
    conversations = get_user_conversations(st.session_state.user_id)

    if not conversations:
        st.sidebar.write("No past assessments found.")
    else:
        # Group conversations by date for a cleaner look
        grouped_convs = defaultdict(list)
        for conv in conversations:
            timestamp_str = conv.get('start_time')
            dt_object = None
            if timestamp_str:
                try:
                    # Robustly parse different timestamp formats
                    ts_clean = timestamp_str.split('+')[0].split('.')[0]
                    dt_object = datetime.strptime(ts_clean, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    dt_object = None
            
            # Determine if the date is Today, Yesterday, or a specific date
            today = date.today()
            if dt_object:
                if dt_object.date() == today:
                    friendly_date_key = "Today"
                elif dt_object.date() == date.fromordinal(today.toordinal() - 1):
                    friendly_date_key = "Yesterday"
                else:
                    friendly_date_key = dt_object.strftime("%B %d, %Y")
            else:
                friendly_date_key = "Unknown Date"
                
            grouped_convs[friendly_date_key].append(conv)
        
        # Display the grouped conversations using expanders
        for friendly_date, conv_list in grouped_convs.items():
            with st.sidebar.expander(f"**{friendly_date}**", expanded=True):
                for conv in conv_list:
                    # Layout with a delete button next to each history item
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
    # Logout button at the bottom
    if st.sidebar.button("Logout", use_container_width=True):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()


def homepage():
    """
    The main dashboard page with action cards and a small calendar preview.
    """
    # Render the sidebar with history
    homepage_sidebar()
    
    # Page title
    st.title(f"Dashboard for {st.session_state.username}")
    st.markdown("Select an action or view your calendar.")
    st.markdown("---")

    # --- TWO-COLUMN LAYOUT for the main content ---
    left_col, right_col = st.columns([0.55, 0.45]) # Left column is slightly wider

    # --- LEFT COLUMN: ACTION CARDS ---
    with left_col:
        st.subheader("Get Started")
        
        # Action Card for Assessment
        with st.container(border=True):
            st.markdown("#### 🧠 Mental Health Assessment")
            st.markdown("Take the PHQ-9 screening to check in with your emotional well-being.")
            if st.button("Start New Assessment", use_container_width=True):
                st.session_state.page = "assessment"
                # Reset state for a fresh assessment
                st.session_state.assessment_active = True
                st.session_state.assessment_conversation_id = None
                st.session_state.assessment_messages = []
                st.session_state.answers = []
                st.session_state.current_question = 0
                st.rerun()

        # Action Card for Schedule Generation
        with st.container(border=True):
            st.markdown("#### ✍️ Generate Self-Care Schedule")
            st.markdown("Get a personalized weekly plan based on your latest assessment results.")
            if st.button("Generate/Update Schedule", use_container_width=True):
                st.session_state.page = "schedule_generator"
                st.rerun()

    # --- RIGHT COLUMN: CALENDAR PREVIEW ---
    with right_col:
        st.subheader("Calendar Preview")
        
        # Inject CSS to make this preview calendar smaller and cleaner
        st.markdown("""
            <style>
            #calendar-preview .fc-view-harness {
                height: 350px !important;
            }
            #calendar-preview .fc-header-toolbar {
                font-size: 0.8em;
                padding: 0;
                margin: 0;
            }
            #calendar-preview .fc-toolbar-title {
                font-size: 1.2em !important;
            }
            </style>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            # Fetch events for the current user
            events = get_calendar_events(st.session_state.user_id)
            
            # Configure calendar options for a non-interactive preview
            calendar_options = {
                "headerToolbar": {
                    "left": "today",
                    "center": "title",
                    "right": "prev,next"
                },
                "initialView": "dayGridMonth",
                "selectable": False,
                "editable": False,
            }
            
            # Wrap the calendar in a div with a unique ID for precise CSS targeting
            st.markdown('<div id="calendar-preview">', unsafe_allow_html=True)
            calendar(events=events, options=calendar_options, key="calendar_preview")
            st.markdown('</div>', unsafe_allow_html=True)

            # Button to navigate to the full, interactive calendar page
            if st.button("Expand & Edit Calendar", use_container_width=True):
                st.session_state.page = "calendar"
                st.rerun()
