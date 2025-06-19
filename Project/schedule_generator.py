import streamlit as st
import google.generativeai as genai
import pandas as pd
import textwrap
import json
import re
from assessment import get_severity_and_feedback
from database import get_latest_assessment_score, get_user_conversations, delete_conversation
from google_calendar import add_events_to_calendar, convert_ai_to_google_events
from collections importOf defaultdict
from datetime import datetime, date

# --- SIDEBAR & HELPERS ---
def get_friendly_date(dt course. Here is the complete code for both `schedule_generator.py` and_object):
    if not dt_object: return "Unknown Date"
    today = date.today()
    if dt_object.date() == today: return "Today"
    if dt_object.date `homepage.py`, fully updated to support the new hybrid authentication model using the Google Calendar API.

These versions correctly() == date.fromordinal(today.toordinal() - 1): return "Yesterday"
    return dt:
-   **Identify the user type** (Google OAuth vs. password-based).
-   Use the appropriate credentials_object.strftime("%B %d, %Y")

def schedule_sidebar():
    """The main sidebar shown on the schedule and assessment pages."""
    st.sidebar.title(f"Welcome, {st.session_state and calendar ID for each type.
-   Delegate all Google Calendar API interactions to the `google_calendar.py.user_data.get('full_name', 'User')}!")
    if st.sidebar.button("🏠 Dashboard` helper module.
-   Provide a clean, user-friendly interface for both generating schedules and viewing the calendar.", use_container_width=True):
        st.session_state.page = "homepage"
        

---

### 1. `schedule_generator.py` (Complete Code)

This file now focuses on gettingst.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Assessment History")
    conversations = get_user_conversations(st.session_state.user_data user preferences, calling the AI to generate a schedule in a specific JSON format, and then passing that structured data to the Google['id'])
    if not conversations:
        st.sidebar.write("No past assessments found.")
    else:
        grouped_convs = defaultdict(list)
        for conv in conversations:
            timestamp_ Calendar helper to be added to the user's calendar.

```python
import streamlit as st
import google.generativeaistr = conv.get('start_time')
            dt_object = None
            if timestamp_str: as genai
import json
import re
from datetime import datetime, date, timedelta
from collections import defaultdict

#
                try:
                    ts = timestamp_str.split('+')[0].split('.')[0]
                    dt Local imports from your project
from database import get_latest_assessment_score, get_user_conversations,_object = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                 delete_conversation
from assessment import get_severity_and_feedback # Assuming this is in assessment.py
fromexcept (ValueError, TypeError): dt_object = None
            friendly_date_key = get_friendly_date google_calendar import add_events_to_calendar, convert_ai_to_google_events

# --- SIDEBAR &(dt_object)
            grouped_convs[friendly_date_key].append(conv)
        
        for friendly_date, conv_list in grouped_convs.items():
            with st.sidebar HELPERS ---
def get_friendly_date(dt_object):
    if not dt_object: return ".expander(f"**{friendly_date}**", expanded=True):
                for conv in convUnknown Date"
    today = date.today()
    if dt_object.date() == today: return_list:
                    col1, col2 = st.columns([0.85, 0.1 "Today"
    if dt_object.date() == date.fromordinal(today.toordinal() -5])
                    with col1:
                        if st.button(f"📜 {conv['title']}", 1): return "Yesterday"
    return dt_object.strftime("%B %d, %Y")

 key=f"conv_{conv['id']}", use_container_width=True):
                            st.sessiondef schedule_sidebar():
    """Renders the sidebar navigation and assessment history."""
    st.sidebar.title(f"_state.page = "assessment"
                            st.session_state.assessment_conversation_id = conv['Welcome, {st.session_state.user_data.get('full_name', 'User')}!")
    id']
                            st.session_state.assessment_messages = []
                            st.session_state.assessment_active = False
                            st.rerun()
                    with col2:
                        if st.button("
    if st.sidebar.button("🏠 Dashboard", use_container_width=True):
        st.session_state.page = "homepage"
        st.rerun()

    st.sidebar.markdown("---")
🗑️", key=f"del_{conv['id']}", use_container_width=True, help=f"Delete    st.sidebar.markdown("### Assessment History")
    
    conversations = get_user_conversations '{conv['title']}'"):
                            delete_conversation(conv['id'])
                            st.toast(f"Deleted '{(st.session_state.user_data['id'])
    if not conversations:
        st.sidebarconv['title']}'.")
                            st.rerun()
    st.sidebar.markdown("---")
.write("No past assessments found.")
    else:
        grouped_convs = defaultdict(list)
    if st.sidebar.button("Logout", use_container_width=True):
        for key in st        for conv in conversations:
            timestamp_str = conv.get('start_time')
            dt_.session_state.keys(): del st.session_state[key]
        st.rerun()

object = None
            if timestamp_str:
                try:
                    ts = timestamp_str.split('+# --- SCHEDULE CORE FUNCTIONS ---
def configure_gemini():
    try:
        genai.configure(')[0].split('.')[0]
                    dt_object = datetime.strptime(ts, '%Y-%m-%api_key=st.secrets.api_keys.google)
        return genai.GenerativeModel("d %H:%M:%S')
                except (ValueError, TypeError): 
                    dt_object = None
gemini-1.5-flash")
    except Exception as e:
        st.error(f"            friendly_date_key = get_friendly_date(dt_object)
            grouped_convs[Failed to configure Gemini: {e}")
        st.stop()

def parse_ai_response_to_friendly_date_key].append(conv)
        
        for friendly_date, conv_list in groupedevents(response_text):
    """Parses the JSON array from the AI's response into a list of event dictionaries."""
    try:
        json_str_match = re.search(r'\[.*\]_convs.items():
            with st.sidebar.expander(f"**{friendly_date}**",', response_text, re.DOTALL)
        if not json_str_match:
            st. expanded=True):
                for conv in conv_list:
                    col1, col2 = st.columns([0.85, 0.15])
                    with col1:
                        if st.buttonerror("The AI did not return a valid schedule format. Please try generating again.")
            st.code(response(f"📜 {conv['title']}", key=f"conv_{conv['id']}", use_container_text)
            return []
        
        events_data = json.loads(json_str_match_width=True):
                            st.session_state.page = "assessment"
                            st.session_.group())
        return events_data
    except (json.JSONDecodeError, AttributeError) as e:
state.assessment_conversation_id = conv['id']
                            st.session_state.assessment_messages =        st.error(f"Error processing the AI's response: {e}")
        st.write("The []
                            st.session_state.assessment_active = False
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{conv['id']}", AI returned the following text, which could not be processed:")
        st.code(response_text)
        return use_container_width=True, help=f"Delete '{conv['title']}'"):
                            delete_ []

def generate_schedule(score, severity, preferences):
    prompt = f"""
    Based on a user'conversation(conv['id'])
                            st.toast(f"Deleted '{conv['title']}'.")
                            s PHQ-9 score of {score}/27 ('{severity}'), and their preferences for "{preferences}", generate ast.rerun()
    st.sidebar.markdown("---")
    if st.sidebar.button(" one-week self-care schedule.
    
    **Instructions:**
    1.  **Adapt to SeverityLogout", use_container_width=True):
        for key in st.session_state.keys():
:** For high scores (>14), activities MUST be very low-effort (e.g., "5-min            del st.session_state[key]
        st.rerun()

# --- SCHEDULE CORE FUNCTIONS --- stretch," "Listen to one song," "Drink a glass of water"). For low scores, they can be more structured
def configure_gemini():
    try:
        genai.configure(api_key=st..
    2.  **Integrate Practical Needs:** Directly include simple, tangible health activities like "Prepare a simple snack (secrets.api_keys.google)
        return genai.GenerativeModel("gemini-1.5e.g., apple slices)" or "Drink a glass of water" into the schedule slots. DO NOT add general-flash")
    except Exception as e:
        st.error(f"Failed to configure Gemini: { notes; put the action in the schedule.
    3.  **Output Format:** Respond ONLY with a JSON arraye}")
        st.stop()

def parse_ai_response_to_events(response_text): of objects. Do not add any introductory text, explanation, or markdown formatting. The entire response must be a valid JSON
    """Parses the JSON array from the AI's response into a list of event dictionaries."""
    try:
         array.
    4.  **JSON Object Keys:** Each object must have these exact keys: "day" (json_str_match = re.search(r'\[.*\]', response_text, re.DOTALLstring, e.g., "Monday"), "activity" (string), "start_time" (string "HH)
        if not json_str_match:
            st.error("AI did not return a valid schedule format.:MM:SS"), "end_time" (string "HH:MM:SS").
    5.   Please try again.")
            st.code(response_text)
            return []
        
        events_data = json**Example Item:** {{"day": "Monday", "activity": "Gentle 5-min morning stretch",.loads(json_str_match.group())
        return events_data
    except (json.JSONDecode "start_time": "08:00:00", "end_time": "08:05:00"}}
    
    Generate a full 7-day schedule with 2-3 activitiesError, AttributeError) as e:
        st.error(f"Error processing AI response: {e}")
        st.write("The AI returned the following text, which could not be processed:")
        st.code(response_ per day.
    """
    model = configure_gemini()
    with st.spinner("Crafting your personalizedtext)
        return []

def generate_schedule(score, severity, preferences):
    prompt = f"""
    Based schedule..."):
        try:
            response = model.generate_content(prompt)
            return response. on a user's PHQ-9 score of {score}/27 ('{severity}'), and their preferencestext
        except Exception as e:
            return f"Error: {e}"

def schedule_generator_page():
    schedule_sidebar()
    st.title("📅 Personalized Self-Care Schedule")
    st.markdown(" for "{preferences}", generate a one-week self-care schedule.
    
    **Instructions:**
    1.  **Adapt to Severity:** For high scores (>14), activities MUST be very low-effort (e.g., "5-Generate a new weekly plan based on your latest assessment. This will add events to your personal Google Calendar.")
    st.markdownmin stretch," "Listen to one song," "Drink a glass of water"). For low scores, they can be more("---")
    
    # Use the logged-in user's ID
    user_id = st.session structured.
    2.  **Integrate Practical Needs:** Directly include simple, tangible health activities like "Prepare a simple snack (_state.user_data['id']
    score = st.session_state.get("last_assessment_e.g., apple slices)" or "Drink a glass of water" into the schedule slots. DO NOT add generalscore")
    
    # If the score isn't in the session, fetch the latest one from the DB notes; put the action in the schedule.
    3.  **Output Format:** Respond ONLY with a JSON array of objects. Do not add any introductory text or explanation. The entire response must be a valid JSON array.
    
    if score is None:
        with st.spinner("Checking for past assessments..."):
            score = get4.  **JSON Object Keys:** Each object must have these exact keys: "day" (string, e._latest_assessment_score(user_id)
        if score is not None:
            st.sessiong., "Monday"), "activity" (string), "start_time" (string "HH:MM:SS_state.last_assessment_score = score
    
    if score is None:
        st.warning"), "end_time" (string "HH:MM:SS").
    5.  **Example Item:** {{"day("You need to complete an assessment first to generate a personalized schedule.")
        if st.button("Go to Assessment"):
": "Monday", "activity": "Gentle 5-min morning stretch", "start_time": "0            st.session_state.page = "assessment"
            st.session_state.assessment_active =8:00:00", "end_time": "08:05:00"}}
 True
            st.session_state.assessment_conversation_id = None
            st.session_state.    
    Generate a full 7-day schedule with 2-3 activities per day.
    """
assessment_messages = []
            st.session_state.answers = []
            st.session_state.    model = configure_gemini()
    with st.spinner("Crafting your personalized schedule..."):
        try:
current_question = 0
            st.rerun()
    else:
        severity, _ = get            response = model.generate_content(prompt)
            return response.text
        except Exception as e:_severity_and_feedback(score)
        st.info(f"Generating a schedule based on your latest assessment score
            return f"Error: {e}"

def schedule_generator_page():
    schedule_sidebar() of **{score}/27** (Severity: **{severity}**).")
        
        preferences =
    st.title("📅 Generate Your Self-Care Schedule")
    st.markdown("Based on your assessment st.text_area("To help me personalize your schedule, what are some things you enjoy or find calming?",
            placeholder="e.g., listening to music, drawing, being in nature, reading, light yoga...")
        , let's create a supportive weekly plan and add it to your personal Google Calendar.")
    st.markdown("
        st.markdown("---")
        if st.button("Generate & Add to My Google Calendar", use---")
    
    # Reliably get the latest score from the database
    score = get_latest_assessment__container_width=True, type="primary"):
            if not preferences:
                st.error("Pleasescore(st.session_state.user_data['id'])
    
    if score is None:
 enter at least one preference to help create a better schedule.")
            else:
                ai_response_text =        st.warning("You need to complete an assessment first to generate a personalized schedule.")
        if st.button generate_schedule(score, severity, preferences)
                ai_events = parse_ai_response_to_events(ai("Go to Assessment"):
            st.session_state.page = "assessment"
            st.session__response_text)
                
                if ai_events:
                    google_events = convert_ai_state.assessment_active = True
            st.session_state.assessment_conversation_id = None
            st.session_state.assessment_messages = []
            st.session_state.answers = []
            to_google_events(ai_events)
                    
                    with st.spinner("Adding events to your calendarst.session_state.current_question = 0
            st.rerun()
    else:
..."):
                        success_count = add_events_to_calendar(google_events)

                    if success_        severity, _ = get_severity_and_feedback(score)
        st.info(f"Generatingcount > 0:
                        st.success(f"Successfully added {success_count} new events to your a schedule based on your latest assessment score of **{score}/27** (Severity: **{severity}**).")
        
        preferences = st.text_area(
            "To help personalize your schedule, what Google Calendar!")
                        st.info("You can view your updated calendar on the Dashboard or directly in your Google Calendar.") are some things you enjoy or find calming?",
            placeholder="e.g., listening to music, drawing, being
                        st.balloons()
                    else:
                        st.error("Could not add events to your calendar. in nature, reading, light yoga..."
        )
        
        if st.button("Generate & Add to My Please ensure you have granted calendar permissions.")
