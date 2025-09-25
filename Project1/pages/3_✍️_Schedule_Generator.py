import streamlit as st
import google.generativeai as genai
import json
import re
from datetime import datetime, timedelta, time
import pandas as pd
from database import (get_calendar_events, save_calendar_events, get_score_trend, get_latest_assessment_answers)
from shared import get_severity_and_feedback
from sidebar import display_sidebar
import textwrap

# --- PAGE GUARD & CONFIG ---
if not st.session_state.get("logged_in"):
    st.error("Please log in to access this page.")
    st.switch_page("app.py")
    st.stop()

# --- INITIALIZE SESSION STATE FOR THIS PAGE ---
if 'preview_schedule' not in st.session_state:
    st.session_state.preview_schedule = None
if 'schedule_time_constraints' not in st.session_state:
    st.session_state.schedule_time_constraints = None
if 'schedule_intensity' not in st.session_state:
    st.session_state.schedule_intensity = "Standard"
if 'schedule_prefs' not in st.session_state:
    st.session_state.schedule_prefs = ""
if 'schedule_focus' not in st.session_state:
    st.session_state.schedule_focus = []

# --- HELPER FUNCTIONS ---
def configure_gemini():
    try:
        genai.configure(api_key=st.secrets.api_keys.google)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")
        st.stop()

# In schedule_generation.py, add this new function near the top

def parse_time_string(time_str):
    """
    Parses a time string from various formats into 'HH:MM:SS'.
    Returns None if parsing fails.
    """
    if not time_str:
        return None
    # Formats to try, from most to least specific
    formats_to_try = [
        '%H:%M:%S',  # '15:30:00'
        '%H:%M',     # '15:30'
        '%I:%M:%S %p', # '3:30:00 PM'
        '%I:%M %p',    # '3:30 PM'
        '%I%p',        # '3PM'
    ]
    for fmt in formats_to_try:
        try:
            # Parse the time string and return it in the desired 24-hour format
            return datetime.strptime(time_str, fmt).strftime('%H:%M:%S')
        except ValueError:
            continue # Try the next format
    return None # Return None if all formats fail

def parse_ai_response_to_events(response_text):
    """Robustly extracts and parses JSON from the AI's response, handling both single objects and arrays."""
    try:
        json_str_match = re.search(r'(\{.*\}|\[.*\])', response_text, re.DOTALL)
        if not json_str_match:
            st.error("AI did not return a valid schedule format (JSON not found).")
            st.code(response_text)
            return None
        
        json_str = json_str_match.group(0)
        if json_str.strip().startswith('{'):
            json_str = f"[{json_str}]"
            
        return json.loads(json_str)
    except Exception as e:
        st.error(f"Error processing AI response: {e}")
        st.code(response_text)
        return None

def generate_schedule(score, severity, trend_context, specific_problems_context, preferences, focus_areas, all_user_events, time_constraints, intensity_context, single_event_to_swap=None):
    fixed_events = [e for e in all_user_events if not e.get('is_generated', True)]
    fixed_events_text = "The user has no fixed commitments."
    if fixed_events:
        event_lines = [f"- On {datetime.fromisoformat(e['start']).strftime('%A')}, '{e['title']}' is from {datetime.fromisoformat(e['start']).strftime('%I:%M %p')} to {datetime.fromisoformat(e['end']).strftime('%I:%M %p')}." for e in fixed_events]
        fixed_events_text = "User's fixed commitments:\n" + "\n".join(event_lines)

    time_constraints_text = "User is available all day."
    if time_constraints:
        constraints = []
        if time_constraints["recurring_block"]["days"] and time_constraints["recurring_block"]["start"] and time_constraints["recurring_block"]["end"]:
            block = time_constraints["recurring_block"]
            constraints.append(f"- Unavailable on {', '.join(block['days'])} from {block['start'].strftime('%I:%M %p')} to {block['end'].strftime('%I:%M %p')}.")
        if time_constraints["sleep"]["start"] and time_constraints["sleep"]["end"]:
            sleep = time_constraints["sleep"]
            constraints.append(f"- Typically asleep from {sleep['start'].strftime('%I:%M %p')} to {sleep['end'].strftime('%I:%M %p')}.")
        if constraints:
            time_constraints_text = "\n".join(constraints)

    main_instructions = "Generate a full 7-day schedule. Respond ONLY with a valid JSON array of objects. Each object in the array MUST contain all of these keys: 'day', 'activity', 'start_time', 'end_time', and 'color'."
    
    if single_event_to_swap:
        activity = single_event_to_swap.get('activity', 'the previous activity')
        day = single_event_to_swap.get('day', 'the same day')
        start_time = single_event_to_swap.get('start_time', 'a similar time')
        main_instructions = f"""
        The user wants to swap this activity: "{activity}". 
        Generate ONE new, DIFFERENT activity for {day} around {start_time}.
        Respond with ONLY a single JSON object. The object MUST contain all of these keys: "day", "activity", "start_time", "end_time", and "color".
        The "day" value MUST be "{day}".
        """

    prompt = f"""
    You are an expert mental health assistant.
    **User's Data:**
    1. Score: {score}/27 ('{severity}')
    2. Trend: {trend_context}
    3. Problem Areas: {specific_problems_context}
    4. Intensity: "{intensity_context}"
    5. Preferences: "{preferences}"
    6. Focus: {', '.join(focus_areas)}
    7. Fixed Commitments: {fixed_events_text}
    8. Unavailable Hours: {time_constraints_text}
    **Instructions:**
    - CRITICAL: Adapt DURATION and COMPLEXITY based on 'Intensity'. "Very Gentle" is 5-10 min tasks.
    - CRITICAL: Place all activities OUTSIDE of unavailable hours/commitments.
    - CRITICAL: Tailor suggestions to 'Problem Areas'.
    - CRITICAL: The 'start_time' and 'end_time' values MUST be in 24-hour 'HH:MM:SS' format (e.g., '09:00:00' or '17:30:00').
    - {main_instructions}
    """
    model = configure_gemini()
    with st.spinner("AI is thinking..."):
        return model.generate_content(prompt).text

def convert_ai_to_calendar_events(ai_events):
    """Converts the AI's day-based schedule to specific calendar dates."""
    calendar_events = []
    today = datetime.now()
    day_map = {day: i for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])}
    for item in ai_events:
        day_str = item.get("day")
        if not day_str or day_str not in day_map: continue
        start_time_str = parse_time_string(item.get("start_time"))
        end_time_str = parse_time_string(item.get("end_time"))

        if not start_time_str or not end_time_str:
            st.warning(f"Could not parse time for event '{item.get('activity')}'. Skipping.")
            continue

        days_ahead = (day_map[day_str] - today.weekday() + 7) % 7
        event_date = (today + timedelta(days=days_ahead)).date()
        days_ahead = (day_map[day_str] - today.weekday() + 7) % 7
        event_date = (today + timedelta(days=days_ahead)).date()
        calendar_events.append({
            "title": item.get("activity"),
            "start": f"{event_date}T{start_time_str}", # Use the parsed time
            "end": f"{event_date}T{end_time_str}",   # Use the parsed time
            "color": item.get("color")
        })
    return calendar_events

display_sidebar() 

# --- MAIN PAGE LOGIC ---
st.title("✍️ AI Schedule Generator")
st.markdown("This AI assistant creates a supportive weekly plan based on your latest assessment, preferences, and availability.")

user_id = st.session_state.user_data['id']
latest_score, previous_score = get_score_trend(user_id)
    
if latest_score is None:
    st.warning("You need to complete an assessment first to generate a personalized schedule.")
    if st.button("Take Assessment Now"): st.switch_page("pages/2_🧠_Assessment.py")
    st.stop()

# --- Data Gathering and Context Formulation ---
severity, _ = get_severity_and_feedback(latest_score)
trend_context = "This is the user's first assessment."
if previous_score is not None:
    if latest_score < previous_score: trend_context = f"IMPROVING (from {previous_score} to {latest_score})."
    elif latest_score > previous_score: trend_context = f"WORSENING (from {previous_score} to {latest_score})."
    else: trend_context = f"STABLE at {latest_score}."

phq9_questions_map = {0:"Little interest or pleasure", 1:"Feeling down/depressed", 2:"Sleep problems", 3:"Feeling tired", 4:"Appetite problems", 5:"Feeling bad about self", 6:"Concentration problems", 7:"Moving/speaking differently", 8:"Thoughts of self-harm"}
latest_answers = get_latest_assessment_answers(user_id)
specific_problems_context = "No specific problem areas identified."
top_problem_key = "default"
if latest_answers:
    scored_questions = sorted(enumerate(latest_answers), key=lambda x: x[1], reverse=True)
    problem_areas = [phq9_questions_map[i] for i, score in scored_questions if score > 1]
    if problem_areas:
        specific_problems_context = "; ".join(problem_areas[:3])
        top_problem_key = problem_areas[0]

# --- Page Flow: Preview or Generate ---
if st.session_state.preview_schedule:
    st.subheader("🗓️ Your Draft Schedule")
    st.info("Review your plan. You can swap individual suggestions or save it to your calendar.")
    
    for i, event in enumerate(st.session_state.preview_schedule):
        with st.container(border=True):
            col1, col2 = st.columns([0.8, 0.2])
            day_display = event.get('day', 'N/A')
            activity_display = event.get('activity', 'Unnamed Activity')
            start_display = event.get('start_time', 'N/A')
            end_display = event.get('end_time', 'N/A')
            col1.markdown(f"**{day_display}:** {activity_display} `({start_display} - {end_display})`")

            if col2.button("Swap 🔄", key=f"swap_{i}", use_container_width=True):
                all_events = get_calendar_events(user_id)
                new_event_text = generate_schedule(
                    latest_score, severity, trend_context, specific_problems_context, 
                    st.session_state.schedule_prefs, st.session_state.schedule_focus, 
                    all_events, st.session_state.schedule_time_constraints, 
                    st.session_state.schedule_intensity, single_event_to_swap=event
                )
                new_event_list = parse_ai_response_to_events(new_event_text)
                
                if new_event_list:
                    newly_swapped_event = new_event_list[0]
                    # --- SAFETY NET LOGIC ---
                    # If the AI forgot a key, fill it in from the original event.
                    if 'day' not in newly_swapped_event:
                        newly_swapped_event['day'] = event.get('day', 'Unknown Day')
                    if 'start_time' not in newly_swapped_event:
                        newly_swapped_event['start_time'] = event.get('start_time', '00:00:00')
                    if 'end_time' not in newly_swapped_event:
                        newly_swapped_event['end_time'] = event.get('end_time', '00:30:00')
                    if 'color' not in newly_swapped_event:
                         newly_swapped_event['color'] = event.get('color', '#6f42c1')

                    st.session_state.preview_schedule[i] = newly_swapped_event
                    st.rerun()
                else:
                    st.error("AI failed to generate a valid replacement. Please try again.")

    st.divider()
    col1, col2 = st.columns(2)
    if col1.button("✅ Save to My Calendar", type="primary", use_container_width=True):
        with st.spinner("Saving events..."):
            calendar_events_to_save = convert_ai_to_calendar_events(st.session_state.preview_schedule)
            if save_calendar_events(user_id, calendar_events_to_save, is_generated=True):
                st.success("Schedule saved!")
                st.session_state.preview_schedule = None
                st.session_state.calendar_force_refresh = True
                st.switch_page("pages/4_📅_Calendar.py")
            else:
                st.error("Failed to save schedule.")
    if col2.button("❌ Start Over", use_container_width=True):
        st.session_state.preview_schedule = None
        st.rerun()
else:
    # --- UI for the Initial Generation State ---
    with st.container(border=True):
        st.subheader("Your Personalization Profile")
        st.markdown(f"- **Latest Score:** `{latest_score}/27` ({severity})")
        st.markdown(f"- **Score Trend:** `{trend_context}`")
        st.markdown(f"- **Top Symptom Areas:** `{specific_problems_context}`")
    
    st.markdown("---")
    
    st.subheader("Step 1: Set Your Pace")
    intensity_map = {1: "Very Gentle", 2: "Gentle", 3: "Standard", 4: "A Little Push", 5: "Motivated"}
    st.session_state.schedule_intensity = st.select_slider("Select the intensity for this week's schedule:", options=list(intensity_map.values()), value=st.session_state.schedule_intensity)

    st.subheader("Step 2: Your Availability")
    with st.expander("Set Unavailable Times (e.g., Work, Sleep)"):
        with st.form("time_constraints_form"):
            days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            st.write("**Recurring Busy Block**")
            block_1_days = st.multiselect("Days:", days_of_week, key="b1_days")
            col1, col2 = st.columns(2)
            block_1_start = col1.time_input("From:", key="b1_start", value=None)
            block_1_end = col2.time_input("Until:", key="b1_end", value=None)
            st.write("**Sleep Schedule (Approximate)**")
            col3, col4 = st.columns(2)
            sleep_start = col3.time_input("Sleep from:", value=time(23, 0), key="sleep_start")
            sleep_end = col4.time_input("Wake up at:", value=time(7, 0), key="sleep_end")
            if st.form_submit_button("Save Availability"):
                st.session_state.schedule_time_constraints = {"recurring_block": {"days": block_1_days, "start": block_1_start, "end": block_1_end}, "sleep": {"start": sleep_start, "end": sleep_end}}
                st.toast("Availability saved!")

    st.subheader("Step 3: Your Self-Care Preferences")
    placeholder_examples = {"Sleep problems": "e.g., reading a book (no screens!), listening to a calm podcast...", "Little interest or pleasure": "e.g., listening to one favorite song, sketching for 5 minutes...", "Feeling tired": "e.g., a 10-minute nap, a glass of cold water...", "default": "e.g., listening to music, being in nature..."}
    st.session_state.schedule_prefs = st.text_area("What are some things you enjoy or find calming?", placeholder=placeholder_examples.get(top_problem_key, placeholder_examples["default"]), value=st.session_state.schedule_prefs)
    st.session_state.schedule_focus = st.multiselect("What are your goals for this week?", ["Mindfulness", "Physical Activity", "Social Connection", "Hobbies", "Productivity"], max_selections=3, default=st.session_state.schedule_focus)
    
    st.markdown("---")
    st.subheader("Step 4: Generate Your Schedule")
    if st.button("Generate Draft Schedule", use_container_width=True, type="primary"):
        if not st.session_state.schedule_prefs or not st.session_state.schedule_focus:
            st.error("Please complete Step 3 (provide preferences and focus areas).")
        else:
            all_events = get_calendar_events(user_id)
            ai_response_text = generate_schedule(latest_score, severity, trend_context, specific_problems_context, st.session_state.schedule_prefs, st.session_state.schedule_focus, all_events, st.session_state.schedule_time_constraints, st.session_state.schedule_intensity)
            ai_events = parse_ai_response_to_events(ai_response_text)
            if ai_events:
                st.session_state.preview_schedule = ai_events
                st.rerun()