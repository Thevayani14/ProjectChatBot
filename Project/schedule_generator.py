import streamlit as st
import google.generativeai as genai
import pandas as pd
import textwrap
from assessment import get_severity_and_feedback # Re-using this helper
from database import get_latest_assessment_score, save_schedule, get_user_conversations, delete_conversation
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
                        if st.button("🗑️", key=f"del_{conv['id']}", use_container_width=True):
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

def generate_schedule(score, severity, feedback, preferences, existing_schedule_df=None):
    existing_schedule_md = ""
    if existing_schedule_df is not None and not existing_schedule_df.empty:
        existing_schedule_md = f"""
        Here is the user's existing schedule of commitments. You MUST schedule the self-care activities AROUND these fixed events.

        {existing_schedule_df.to_markdown(index=False)}
        """

    prompt = f"""
    You are an expert and empathetic mental health assistant. Your task is to create a supportive and realistic one-week self-care schedule for a user.
    **User's Data:**
    1.  **PHQ-9 Score:** {score}/27
    2.  **Severity Level:** '{severity}'
    3.  **Initial Feedback Provided to User:** {feedback}
    4.  **User's Self-Care Preferences:** "{preferences}"
    5.  **User's Existing Commitments (Work/Study):**
        {existing_schedule_md if existing_schedule_md else "The user has not provided a fixed schedule. Assume they have a standard flexible schedule."}
    **Your Instructions:**
    - **Integrate, Don't Overwrite:** Build the self-care schedule AROUND the user's existing commitments. Fill in the free time (mornings, afternoons, evenings) where they don't have a fixed event.
    - **Adapt to Severity:** The schedule must be appropriate for the severity level.
        - For 'Mild' scores, you can suggest more structured activities.
        - For 'Moderate' to 'Severe' scores, suggest very small, low-effort, high-reward tasks. Examples: "Sit by a window for 5 mins," "Listen to one favorite song," "Drink a glass of water," "Gentle 5-minute stretch." The goal is to build momentum, not create pressure.
        - If the score is high (e.g., > 14) and preferences include screen-based activities like "playing games," gently moderate them. Suggest "Play one round of a favorite game (about 20 mins)" instead of "Game for 2 hours."
    - **Use Feedback and Preferences:** Incorporate activities related to the user's stated preferences and the initial feedback provided. For example, if the feedback mentioned connection, suggest "Text one friend 'hello'."
    - **Format:** The final output must be a markdown table with columns: Day, Morning, Afternoon, Evening.
    - **Tone:** Start with an empathetic and encouraging opening sentence. Do not be preachy. Be a supportive companion.
    """
    model = configure_gemini()
    with st.spinner("Crafting your personalized and integrated schedule..."):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Sorry, I encountered an error while generating your schedule: {e}"

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
        severity, feedback = get_severity_and_feedback(score)
        st.info(f"Generating a schedule based on your latest assessment score of **{score}/27** (Severity: **{severity}**).")
        
        preferences = st.text_area("To help me personalize your schedule, what are some things you enjoy or find calming?",
            placeholder="e.g., listening to music, drawing, being in nature, reading, light yoga...")
        st.markdown("---")
        
        st.subheader("Upload Existing Schedule (Optional)")
        st.markdown("Upload a CSV file with your work, study, or other fixed commitments. Columns could be `Day`, `Time`, `Activity`.")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        existing_schedule_df = None
        if uploaded_file is not None:
            try:
                existing_schedule_df = pd.read_csv(uploaded_file)
                st.write("Your uploaded schedule:")
                st.dataframe(existing_schedule_df)
            except Exception as e:
                st.error(f"Error reading the file: {e}")

        st.markdown("---")
        if st.button("Generate My Integrated Schedule", use_container_width=True, type="primary"):
            if not preferences:
                st.error("Please enter at least one preference.")
            else:
                schedule_md = generate_schedule(score, severity, feedback, preferences, existing_schedule_df)
                if save_schedule(st.session_state.user_id, schedule_md):
                    st.toast("Schedule saved successfully!")
                else:
                    st.toast("Error: Could not save schedule.")
                st.session_state.generated_schedule = schedule_md
                st.rerun()
        
        if "generated_schedule" in st.session_state:
            st.markdown("### Your Personalized Schedule")
            st.markdown(st.session_state.generated_schedule)
