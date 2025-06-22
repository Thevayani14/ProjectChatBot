import streamlit as st
from collections import defaultdict
from datetime import datetime, date
from database import get_user_conversations, delete_conversation

def sidebar():
    """Renders the main sidebar for the application after a user is logged in."""
    if 'user_data' not in st.session_state or st.session_state.user_data is None:
        st.switch_page("app.py")

    display_name = st.session_state.user_data.get('full_name') or st.session_state.user_data.get('username')
    st.sidebar.title(f"Welcome, {display_name}!")
    st.sidebar.markdown("---")

    st.sidebar.page_link("pages/1_🏠_Homepage.py", label="Dashboard", icon="🏠")
    st.sidebar.page_link("pages/2_🧠_Assessment.py", label="New Assessment", icon="🧠")
    st.sidebar.page_link("pages/3_✍️_Schedule_Generator.py", label="Generate Schedule", icon="✍️")

    with st.sidebar.expander("📜 Assessment History", expanded=False):
        conversations = get_user_conversations(st.session_state.user_data['id'])
        if not conversations:
            st.write("No past assessments.")
        else:
            # (Your logic for grouping and displaying conversations here)
            # Example:
            for conv in conversations:
                st.page_link("pages/2_🧠_Assessment.py", label=f"📜 {conv['title']}", 
                              query_params={"conversation_id": conv['id']})

    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_data = None
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
