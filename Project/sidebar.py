import streamlit as st
from database import get_user_conversations, delete_conversation # Still need both functions
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
    Includes a one-click delete option for each conversation.
    """
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")
    
    if st.sidebar.button("🏠 Home", use_container_width=True):
        st.session_state.page = "homepage"
        if "assessment_active" in st.session_state: del st.session_state.assessment_active
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Assessment History")

    conversations = get_user_conversations(st.session_state.user_id)

    if not conversations:
        st.sidebar.write("No past assessments found.")
    else:
        grouped_convs = defaultdict(list)
        for conv in conversations:
            timestamp_str = conv.get('start_time')
            dt_object = None
            if timestamp_str:
                try:
                    if '+' in timestamp_str: timestamp_str = timestamp_str.split('+')[0]
                    if '.' in timestamp_str: timestamp_str = timestamp_str.split('.')[0]
                    dt_object = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    dt_object = None
            friendly_date_key = get_friendly_date(dt_object)
            grouped_convs[friendly_date_key].append(conv)
        
        # Display the grouped conversations
        for friendly_date, conv_list in grouped_convs.items():
            with st.sidebar.expander(f"**{friendly_date}**", expanded=True):
                for conv in conv_list:
                    conv_id = conv['id']
                    title = conv.get('title', 'Assessment')

                    # --- SIMPLIFIED: ONE-CLICK DELETE LOGIC ---
                    col1, col2 = st.columns([0.85, 0.15]) # Main button gets 85% of space
                    
                    with col1:
                        if st.button(f"📜 {title}", key=f"conv_{conv_id}", use_container_width=True):
                            st.session_state.page = "assessment"
                            st.session_state.assessment_conversation_id = conv_id
                            st.session_state.assessment_messages = []
                            st.session_state.assessment_active = False
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️", key=f"del_{conv_id}", use_container_width=True, help=f"Delete '{title}'"):
                            # Call the delete function directly
                            if delete_conversation(conv_id):
                                st.toast(f"Deleted '{title}'.")
                            else:
                                st.toast(f"Error deleting '{title}'.")
                            # Rerun the app to refresh the history list
                            st.rerun()
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
