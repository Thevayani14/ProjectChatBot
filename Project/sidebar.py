import streamlit as st
from collections import defaultdict
from datetime import datetime, date, timedelta
from database import (
    get_todays_events,
    get_user_conversations,
    delete_conversation,
    clear_all_assessments
)
import requests

@st.cache_data(ttl=3600)
def fetch_gaming_news():
    """
    Fetches gaming and wellness news using a fallback system.
    It tries the primary API (News API) first. If it fails or returns no articles,
    it automatically tries the secondary API (GNews).
    """
    
    # --- 1. TRY THE PRIMARY SOURCE: News API ---
    print("DEBUG: Attempting to fetch news from Primary Source (News API)...")
    try:
        api_key = st.secrets.api_keys.newsapi
        query = '(gaming AND (wellness OR "mental health"))'
        from_date = (date.today() - timedelta(days=30)).isoformat()
        
        url = (
            "https://newsapi.org/v2/everything?"
            f"q={query}&"
            f"from={from_date}&"
            "language=en&"
            "sortBy=relevancy&"
            f"apiKey={api_key}"
        )
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "ok" and data.get("articles"):
            articles = data.get("articles", [])
            print(f"SUCCESS: Fetched {len(articles)} articles from News API.")
            return articles[:6] # Return the successful result and stop.
            
    except Exception as e:
        print(f"WARN: Primary Source (News API) failed. Reason: {e}")
    
    # --- 2. IF PRIMARY FAILED, TRY THE FALLBACK SOURCE: GNews ---
    print("\nDEBUG: Primary source failed. Attempting to fetch news from Fallback Source (GNews)...")
    try:
        api_key = st.secrets.api_keys.gnews
        query = 'gaming "mental health" OR gaming wellness'
        
        url = f"https://gnews.io/api/v4/search?q={query}&lang=en&max=6&apikey={api_key}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])
        
        if articles:
            print(f"SUCCESS: Fetched {len(articles)} articles from GNews.")
            return articles # Return the successful fallback result.
        else:
            print("WARN: Fallback Source (GNews) also returned no articles.")

    except Exception as e:
        print(f"FATAL: Fallback Source (GNews) also failed. Reason: {e}")

    # --- 3. IF BOTH FAILED ---
    print("FATAL: Both news APIs failed. Returning empty list.")
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

        if page_name == "assessment": 
            _display_assessment_history(st.session_state.user_data['id'])
        elif page_name in ["behaviour", "emotion", "suggestion"]: 
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
        if st.button("Logout", use_container_width=True, key="homepage_logout"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.switch_page("app.py")