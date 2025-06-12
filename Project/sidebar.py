import streamlit as st
from database import get_user_conversations

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
            if st.sidebar.button(f"📜 {title}", key=f"conv_{conv['id']}", use_container_width=True):
                # When a past assessment is clicked, switch to the assessment page
                # and load its data.
                st.session_state.page = "assessment"
                st.session_state.assessment_conversation_id = conv['id']
                st.session_state.assessment_active = False # View mode, not active questioning
                st.rerun()
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        # Clear all session data to log out
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()