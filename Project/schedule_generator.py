import streamlit as st
import google.generativeai as genai
import pandas as pd
import textwrap
import json
import re
from assessment import get_severity_and_feedback
from database import get_latest_assessment_score, save_calendar_events, get_user_conversations, delete_conversation
from collections import defaultdict
from datetime import datetime, date

# --- SIDEBAR & HELPERS ---
def get_friendly_date(dt_object):
    if not dt_object: return "Unknown Date"
    today = date.today()
    if dt_object.date() == today: return "Today"
    if dt_object.date() == date.fromordinal(today.toordinal() - 1): return "Yesterday"
    return dt_object.strftime("%B %d, %Y")

def schedule_sidebar():
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    if st.sidebar.button("🏠 Home", use_container_width=True):
        st.session_state.page = "homepage"
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
                    ts = timestamp_str.split('+')[0].split('.')[0]
                    dt_object = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError): dt_object = None
            friendly_date_key = get_friendly_date(dt_object)
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
                        if st.button("🗑️", key=f"del_{conv['id']}", use_container_width=True, help=f"Delete '{conv['title']}'"):
                            delete_conversation(conv['id'])
                            st.toast(f"Deleted '{conv['title']}'.")
                            st.rerun()
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", use_container_width=True):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

# --- SCHEDULE CORE FUNCTIONS ---
def configure_gemini():
    try:
        genai.configure(api_key=st.secrets.api_keys.google)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")
        st.stop()

def parse_ai_response_to_events(response_text):
    """Parses the JSON array from the AI's response into a list of event dictionaries."""
    try:
        json_str_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if not json_str_match:
            st.error("AI did not return a valid schedule format. Please try again.")
            st.code(response_text)
            return []
        
        events_data = json.loads(json_str_match.group())
        return events_data
    except (json.JSONDecodeError, AttributeError) as e:
        st.error(f"Error processing AI response: {e}")
        st.write("The AI returned the following text, which could not be processed:")
        st.code(response_text)
        return []

def generate_schedule(score, severity, preferences):
    prompt = f"""
    Based on a user's PHQ-9 score of {score}/27 ('{severity}'), and their preferences for "{preferences}", generate a one-week self-care schedule.
    
    **Instructions:**
    1.  **Adapt to Severity:** For high scores (>14), activities MUST be very low-effort (e.g., "5-min stretch," "Listen to one song," "Drink a glass of water"). For low scores, they can be more structured.
    2.  **Integrate Practical Needs:** Directly include simple, tangible health activities like "Prepare a simple snack (e.g., apple slices)" or "Drink a glass of water" into the schedule slots. DO NOT add general notes; put the action in the schedule.
    3.  **Output Format:** Respond ONLY with a JSON array of objects. Do not add any introductory text or explanation. The entire response must be a valid JSON array.
    4.  **JSON Object Keys:** Each object must have these exact keys: "day" (string, e.g., "Monday"), "activity" (string), "start_time" (string "HH:MM:SS"), "end_time" (string "HH:MM:SS"), and "color" (a hex code like "#20c997").
    5.  **Example Item:** {{"day": "Monday", "activity": "Gentle 5-min morning stretch", "start_time": "08:00:00", "end_time": "08:05:00", "color": "#fd7e14"}}
    
    Generate a full 7-day schedule with 2-3 activities per day.
    """
    model = configure_gemini()
    with st.spinner("Crafting your personalized schedule..."):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {e}"

def convert_ai_to_calendar_events(ai_events):
    """Converts the AI's list of events to the format needed for saving and calendar display."""
    calendar_events = []
    today = datetime.now()
    day_map = {day: i for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])}

    for item in ai_events:
        day_str = item.get("day")
        if not day_str or day_str not in day_map: continue

        days_ahead = (day_map[day_str] - today.weekday() + 7) % 7
        event_date = (today + pd.Timedelta(days=days_ahead)).date()

        calendar_events.append({
            "title": item.get("activity"),
            "start": f"{event_date}T{item.get('start_time')}",
            "end": f"{event_date}T{item.get('end_time')}",
            "color": item.get("color")
        })
    return calendar_events

def schedule_generator_page():
    schedule_sidebar()
    st.title("📅 Personalized Self-Care Schedule")
    st.markdown("---")
    
    score = st.session_state.get("last_assessment_score")
    if score is None:
        with st.spinner("Checking for past assessments..."):
            score = get_latest_assessment_score(st.session_state.user_id)
        if score is not None:
            st.session_state.last_assessment_score = score
    
    if score is None:
        st.warning("You need to complete an assessment first to generate a personalized schedule.")
        if st.button("Go to Assessment"):
            st.session_state.page = "assessment"
            st.session_state.assessment_active = True
            st.session_state.assessment_conversation_id = None
            st.session_state.assessment_messages = []
            st.session_state.answers = []
            st.session_state.current_question = 0
            st.rerun()
    else:
        severity, _ = get_severity_and_feedback(score)
        st.info(f"Generating a schedule based on your latest assessment score of **{score}/27** (Severity: **{severity}**).")
        
        preferences = st.text_area("To help me personalize your schedule, what are some things you enjoy or find calming?",
            placeholder="e.g., listening to music, drawing, being in nature, reading, light yoga...")
        
        st.markdown("---")
        if st.button("Generate My Schedule", use_container_width=True, type="primary"):
            if not preferences:
                st.error("Please enter at least one preference.")
            else:
                ai_response_text = generate_schedule(score, severity, preferences)
                ai_events = parse_ai_response_to_events(ai_response_text)
                
                if ai_events:
                    calendar_events_to_save = convert_ai_to_calendar_events(ai_events)
                    if save_calendar_events(st.session_state.user_id, calendar_events_to_save, is_generated=True):
                        st.success("Your schedule has been generated! Go to the Home page to see it on your calendar.")
                        st.balloons()
                    else:
                        st.error("Could not save your schedule to the database.")
