import streamlit as st
from database import get_user_conversations
from datetime import datetime, date
from collections import defaultdict

def get_friendly_date(dt_object):
    """Converts a datetime object to a user-friendly string like 'Today', 'Yesterday', or 'Dec 25, 2023'."""
    if not dt_object:
        return "Unknown Date"
    today = date.today()
    if dt_object.date() == today:
        return "Today"
    if dt_object.date() == date.fromordinal(today.toordinal() - 1):
        return "Yesterday"
    return dt_object.strftime("%B %d, %Y")

def show_sidebar():
    """
    Displays the sidebar with user info, logout, and conversation history grouped by date.
    """
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")
    
    if st.sidebar.button("🏠 Home", use_container_width=True):
        st.session_state.page = "homepage"
        if "assessment_active" in st.session_state:
            del st.session_state.assessment_active
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Assessment History")

    conversations = get_user_conversations(st.session_state.user_id)

    if not conversations:
        st.sidebar.write("No past assessments found.")
    else:
        # Group conversations by date
        grouped_convs = defaultdict(list)
        for conv in conversations:
            timestamp_str = conv.get('start_time')
            dt_object = None # Initialize as None
            
            if timestamp_str:
                try:
                    # More robust parsing for different timestamp formats
                    if '+' in timestamp_str: timestamp_str = timestamp_str.split('+')[0]
                    if '.' in timestamp_str: timestamp_str = timestamp_str.split('.')[0]
                    dt_object = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    # If parsing fails for any reason, dt_object remains None
                    dt_object = None
            
            # Use the helper function to get the key for our dictionary
            friendly_date_key = get_friendly_date(dt_object)
            grouped_convs[friendly_date_key].append(conv)
        
        # Display the grouped conversations
        for friendly_date, conv_list in grouped_convs.items():
            # Use an expander for each date group for better organization
            with st.sidebar.expander(f"**{friendly_date}**", expanded=True):
                for conv in conv_list:
                    title = conv.get('title', 'Assessment')
                    if st.button(f"📜 {title}", key=f"conv_{conv['id']}", use_container_width=True):
                        st.session_state.page = "assessment"
                        st.session_state.assessment_conversation_id = conv['id']
                        st.session_state.assessment_messages = []
                        st.session_state.assessment_active = False
                        st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
