import streamlit as st
from database import get_user_conversations
from datetime import datetime # Import the datetime module

def show_sidebar():
    """
    Displays the sidebar with user info, logout, and conversation history.
    Handles navigation when a past conversation is clicked.
    """
    st.sidebar.title(f"Welcome, {st.session_state['username']}!")
    
    if st.sidebar.button("🏠 Home", use_container_width=True):
        st.session_state.page = "homepage"
        # Reset any active assessment state when going home
        if "assessment_active" in st.session_state:
            del st.session_state.assessment_active
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Assessment History")

    # Load and display conversation history
    conversations = get_user_conversations(st.session_state.user_id)
    if not conversations:
        st.sidebar.write("No past assessments found.")
    else:
        for conv in conversations:
            # Use a more descriptive title if available, otherwise use a generic one
            title = conv.get('title', 'Assessment')
            
            # --- NEW: FORMAT AND DISPLAY THE TIMESTAMP ---
            # Get the timestamp string from the conversation data
            timestamp_str = conv.get('start_time')
            
            # Create a container for the button and the date
            with st.sidebar.container():
                if st.button(f"📜 {title}", key=f"conv_{conv['id']}", use_container_width=True):
                    # When a past assessment is clicked, switch to the assessment page
                    # and load its data.
                    st.session_state.page = "assessment"
                    st.session_state.assessment_conversation_id = conv['id']
                    st.session_state.assessment_messages = [] # Clear messages to force a reload
                    st.session_state.assessment_active = False # View mode, not active questioning
                    st.rerun()

                if timestamp_str:
                    # Parse the timestamp string. The format might vary slightly depending on the DB.
                    # This format handles the typical ISO 8601 format from Supabase/PostgreSQL.
                    # It will look like: 2023-10-27T08:30:00+00:00
                    # We strip the timezone info for simplicity in parsing.
                    try:
                        # Handle potential timezone offsets like +00:00
                        if '+' in timestamp_str:
                            timestamp_str = timestamp_str.split('+')[0]
                        
                        # Handle potential fractional seconds
                        if '.' in timestamp_str:
                             timestamp_str = timestamp_str.split('.')[0]

                        dt_object = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        # Format it into a user-friendly string (e.g., "Oct 27, 2023")
                        friendly_date = dt_object.strftime("%b %d, %Y")
                        
                        # Display the date below the button using markdown for styling
                        st.markdown(f"<p style='text-align: right; color: #888; font-size: 0.8em; margin-top: -10px; margin-bottom: 10px;'>{friendly_date}</p>", unsafe_allow_html=True)
                    except ValueError:
                        # If parsing fails for any reason, just show a dash or nothing
                        st.markdown(f"<p style='text-align: right; color: #888; font-size: 0.8em; margin-top: -10px; margin-bottom: 10px;'>-</p>", unsafe_allow_html=True)

    
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        # Clear all session data to log out
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
