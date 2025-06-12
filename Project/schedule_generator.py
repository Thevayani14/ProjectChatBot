# schedule_generator.py

import streamlit as st
import google.generativeai as genai
from assessment import get_severity_and_feedback # Import helper from assessment module
from sidebar import show_sidebar

def configure_gemini():
    try:
        genai.configure(api_key=st.secrets.api_keys.google)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")
        st.stop()

def generate_schedule(score, severity, preferences):
    model = configure_gemini()
    prompt = f"""
    Based on a user's PHQ-9 depression screening score of {score}/27, which indicates '{severity}' depression, and their stated preferences, generate a supportive and realistic one-week self-care schedule.

    User Preferences: "{preferences}"

    The schedule should:
    - Be formatted as a markdown table with columns: Day, Morning, Afternoon, Evening.
    - Be gentle and not overwhelming. For higher scores, suggest very small, manageable tasks (e.g., "Step outside for 5 minutes" instead of "Go for a 1-hour run").
    - Incorporate activities related to the user's preferences.
    - Include a mix of activities for physical well-being (e.g., gentle stretching, short walk), mental well-being (e.g., 5-minute mindfulness, journaling), and simple pleasures (e.g., listening to a favorite song, drinking tea).
    - For scores above 14, gently weave in reminders to connect with a friend, family member, or a professional.
    - Start with an empathetic and encouraging opening sentence before the table.
    """
    
    with st.spinner("Crafting your personalized schedule..."):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Sorry, I encountered an error while generating your schedule: {e}"

def schedule_generator_page():
    show_sidebar()
    st.title("📅 Personalized Self-Care Schedule")
    st.markdown("---")
    
    # Check if user has completed an assessment
    if "last_assessment_score" not in st.session_state:
        st.warning("You need to complete an assessment first to generate a personalized schedule.")
        if st.button("Go to Assessment"):
            st.session_state.page = "assessment"
            st.rerun()
    else:
        score = st.session_state.last_assessment_score
        severity, _ = get_severity_and_feedback(score)
        
        st.info(f"Generating a schedule based on your last assessment score of **{score}/27** (Severity: **{severity}**).")
        
        preferences = st.text_area(
            "To help me personalize your schedule, what are some things you enjoy or find calming?",
            placeholder="e.g., listening to music, drawing, being in nature, reading, light yoga..."
        )
        
        if st.button("Generate My Schedule", use_container_width=True):
            if not preferences:
                st.error("Please enter at least one preference to help me create a better schedule for you.")
            else:
                schedule = generate_schedule(score, severity, preferences)
                st.markdown(schedule)
