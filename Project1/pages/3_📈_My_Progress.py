# In 3_📈_My_Progress.py, REPLACE the entire file content with this:

import streamlit as st
import pandas as pd
import google.generativeai as genai
from shared import display_progress_dashboard, get_scores_over_time
from database import get_scores_over_time # Re-importing here for clarity
import textwrap

# --- Page Config & Login Check ---
st.set_page_config(layout="wide", page_title="My Progress")

if not st.session_state.get("logged_in"):
    st.error("Please log in to view your progress.")
    st.switch_page("app.py")
    st.stop()
    
# --- Helper for AI analysis ---
def configure_gemini():
    try:
        genai.configure(api_key=st.secrets.api_keys.google)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"Failed to configure Gemini for analysis: {e}")
        return None

def get_ai_trend_analysis(df):
    """Generates a narrative summary of the user's progress using AI."""
    model = configure_gemini()
    if not model:
        return "Could not generate AI analysis at this time."

    # Format the data for the prompt
    prompt_data = df[['Date', 'Score']].to_string(index=False, header=True)
    
    prompt = textwrap.dedent(f"""
        You are a compassionate and insightful mental health assistant.
        Analyze the following PHQ-9 score progression for a user.
        A score of 0-4 is minimal, 5-9 is mild, 10-14 is moderate, 15-19 is moderately severe, and 20+ is severe.

        User's Data (Date, Score):
        {prompt_data}

        Your task is to provide a brief, supportive, and insightful summary (2-3 paragraphs).
        - Identify the overall trend (e.g., "steady improvement," "experiencing some ups and downs," "worsening trend").
        - Mention the highest and lowest scores in the period as key data points.
        - Offer encouragement based on their journey. For example, if they improved, praise their effort. If they had a setback after a period of doing well, acknowledge that recovery is not always linear.
        - If the trend is worsening or scores are consistently high, express gentle concern and suggest they review the resources provided or consider creating a new self-care schedule.
        - **Crucially, do not give medical advice.** Keep the tone warm, empowering, and focused on patterns.
        - Respond in well-formatted markdown.
    """)
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred during AI analysis: {e}"


# --- Main Page Content ---
st.title("📈 Wellness Dashboard")
st.markdown("Track your mental wellness journey, identify patterns, and find helpful resources.")
st.divider()

user_id = st.session_state.user_data['id']
score_data = get_scores_over_time(user_id)

tab1, tab2 = st.tabs(["📊 Main Dashboard", "🤖 AI Analysis & Reflection"])

with tab1:
    # The main dashboard component is now self-contained and powerful
    display_progress_dashboard(user_id)

with tab2:
    st.header("AI-Powered Trend Analysis")
    st.markdown("Get an AI-generated summary of your progress in the selected period to help you understand your journey better.")

    if score_data.empty or len(score_data) < 2:
         st.info("You need at least two assessments to generate an AI trend analysis.")
    else:
        if st.button("✨ Generate My AI Summary", use_container_width=True, type="primary"):
            with st.spinner("🤖 Your personal AI is analyzing your trends..."):
                analysis_text = get_ai_trend_analysis(score_data)
                st.session_state.ai_analysis = analysis_text
        
        if 'ai_analysis' in st.session_state:
            with st.container(border=True):
                st.markdown(st.session_state.ai_analysis)

    st.divider()
    with st.container(border=True):
        st.subheader("Reflection & Action")
        st.markdown("""
        Use your dashboard and the AI analysis to reflect on your journey. Understanding your patterns is the first step toward managing your well-being.
        - **Look at the peaks:** What was happening during times of higher scores? Was it stress from work, lack of sleep, or something else?
        - **Look at the valleys:** What contributed to your better days? More exercise, social connection, a specific accomplishment?
        
        **What's one small, kind action you can take for yourself today based on what you see?**
        """)