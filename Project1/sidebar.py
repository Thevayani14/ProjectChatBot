# sidebar.py (Corrected Version)

import streamlit as st
from collections import defaultdict
from datetime import datetime, date, timedelta
# Import all necessary database functions here
from database import (
    get_todays_events,
    get_user_conversations,
    delete_conversation,
    clear_all_assessments
)
import requests

# (All helper functions like fetch_gaming_news and _display_assessment_history remain the same)
@st.cache_data(ttl=3600)
def fetch_gaming_news():
    try:
        api_key = st.secrets.api_keys.gnews
        query = '("video games" AND "mental health") OR ("gaming" AND "wellness")'
        url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=6&apikey={api_key}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("articles", [])
    except Exception as e:
        print(f"Error fetching GNews: {e}")
        return []

def _display_assessment_history(user_id):
    st.sidebar.header("Assessment History")
    all_conversations = get_user_conversations(user_id)
    assessments = [conv for conv in all_conversations if conv.get('title', '').startswith("PHQ-9 Assessment")]
    if not assessments:
        st.sidebar.info("No past assessments found.")
    else:
        for assessment in assessments:
            with st.sidebar.container():
                score = assessment.get('completion_score')
                score_text = f"(Score: {score})" if score is not None else "(Incomplete)"
                col1, col2 = st.columns([0.8, 0.2])
                if col1.button(f"{assessment['title']} *{score_text}*", key=f"view_{assessment['id']}", use_container_width=True):
                    st.session_state.viewing_assessment = assessment
                    if 'assessment_status' in st.session_state: del st.session_state.assessment_status
                    st.rerun()
                if col2.button("🗑️", key=f"delete_{assessment['id']}", use_container_width=True):
                    delete_conversation(assessment['id'])
                    if st.session_state.get('viewing_assessment') and st.session_state.viewing_assessment['id'] == assessment['id']:
                        st.session_state.viewing_assessment = None
                    st.rerun()
            st.sidebar.divider()
    with st.sidebar.container(border=True):
        if st.session_state.get('confirming_clear_assessments', False):
            st.warning("This will permanently delete ALL assessment history.")
            c1, c2 = st.columns(2)
            if c1.button("Yes, Delete All", type="primary", use_container_width=True):
                with st.spinner("Deleting history..."):
                    if clear_all_assessments(user_id):
                        st.toast("Assessment history cleared.")
                        st.session_state.confirming_clear_assessments = False
                        st.session_state.viewing_assessment = None
                        st.rerun()
            if c2.button("Cancel", use_container_width=True):
                st.session_state.confirming_clear_assessments = False
                st.rerun()
        else:
            if assessments:
                if st.button("Clear All History", use_container_width=True):
                    st.session_state.confirming_clear_assessments = True
                    st.rerun()
            else:
                st.caption("No assessment history to clear.")

# --- MAIN SIDEBAR: FOR ALL PAGES EXCEPT LOGIN ---
def display_sidebar(page_name=""):
    with st.sidebar:
        display_name = st.session_state.user_data.get('username')
        st.title(f"Welcome, {display_name}!")
        st.divider() # Added for better visual separation

        if page_name == "assessment": # <-- Correct indentation
            _display_assessment_history(st.session_state.user_data['id'])
        elif page_name in ["behaviour", "emotion", "suggestion"]: # <-- Correct indentation
            st.info(f"You are viewing the {page_name.title()} tool.")

        st.markdown('<div style="margin-top: 2rem;"></div>', unsafe_allow_html=True)
        st.divider()
        if st.button("Logout", use_container_width=True, key="main_sidebar_logout"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.switch_page("app.py")


# --- HOMEPAGE-ONLY SIDEBAR ---
def display_homepage_sidebar():
    with st.sidebar:
        display_name = st.session_state.user_data.get('username')
        st.title(f"Welcome, {display_name}!")
        st.divider()
        st.subheader("Today's Focus ✨")
        today = date.today()
        todays_events = get_todays_events(st.session_state.user_data['id'], today)
        with st.container(border=True):
            if not todays_events:
                st.write("No activities scheduled for today. Time to relax!")
            else:
                for event in todays_events:
                    title, start_time = event
                    if start_time:
                        time_str = start_time.strftime("%I:%M %p").lstrip('0')
                        st.markdown(f"**{time_str}:** {title}")
                    else:
                        st.markdown(f"**All-day:** {title}")
        st.divider()
        st.subheader("Gaming & Wellness Feed 🎮")
        news_articles = fetch_gaming_news()
        if not news_articles:
            st.info("Could not fetch news at this time.")
        else:
            for article in news_articles:
                with st.container(border=True):
                    st.markdown(f"**[{article['title']}]({article['url']})**")
                    st.caption(f"Source: {article['source']['name']}")
        st.divider()
        # --- THIS IS THE FIX ---
        # Ensure this key is different from the other sidebar's logout button.
        if st.button("Logout", use_container_width=True, key="homepage_logout"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.switch_page("app.py")