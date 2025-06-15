import streamlit as st
import google.generativeai as genai
import textwrap
from database import add_message, get_messages, create_conversation, update_conversation_title, get_user_conversations
from sidebar import show_sidebar

# --- HELPER FUNCTIONS ---
def configure_gemini():
    """Configures the Gemini model from secrets."""
    try:
        genai.configure(api_key=st.secrets.api_keys.google)
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}. Please check your API key.")
        st.stop()

def initialize_assessment_session():
    """Initializes session state variables for the assessment if they don't exist."""
    if "assessment_messages" not in st.session_state: st.session_state.assessment_messages = []
    if "assessment_conversation_id" not in st.session_state: st.session_state.assessment_conversation_id = None
    if "assessment_active" not in st.session_state: st.session_state.assessment_active = True
    if "current_question" not in st.session_state: st.session_state.current_question = 0
    if "answers" not in st.session_state: st.session_state.answers = []

def get_severity_and_feedback(total_score):
    """Returns the severity level and detailed feedback based on the PHQ-9 score."""
    if total_score <= 4:
        return "Minimal or None", textwrap.dedent("""*   **Positive Reinforcement:** You're doing great! Keep it up! 🌱 *   **Continued Self-Care:** Continue to prioritize activities that support your well-being.""")
    elif 5 <= total_score <= 9:
        return "Mild", textwrap.dedent("""*   **Lifestyle Suggestions:** Consider focusing on areas like sleep hygiene or a healthy balance with screen time. *   **Self-Care Techniques:** This is a good time to be proactive with journaling or relaxation exercises.""")
    elif 10 <= total_score <= 14:
        return "Moderate", textwrap.dedent("""*   **Stress Management:** Your score suggests notable stress. Techniques from CBT can be very effective. *   **Encourage Connection:** Please consider talking to a trusted friend or family member.""")
    elif 15 <= total_score <= 19:
        return "Moderately Severe", textwrap.dedent("""*   **Encourage Professional Help:** I strongly encourage you to consider speaking with a therapist or counselor. *   **Guided Exercises:** Structured exercises like guided meditations can provide stability.""")
    else: # 20 <= total_score <= 27
        return "Severe", """<div style="border: 2px solid #FF4B4B; border-radius: 10px; padding: 1rem; background-color: #FFF0F0;"><h3 style="color: #D32F2F;">A Gentle Check-In...</h3><p>Your answers suggest you might be going through a particularly tough time. The most important thing is your safety.</p><p><strong>You are not alone, and immediate help is available. Please connect with someone right away:</strong></p><ul><li><strong>Talk or Text:</strong> Call or text <b>988</b> anytime in the US & Canada.</li><li><strong>Medical Support:</strong> Contact a doctor or therapist.</li></ul></div>"""

# --- UI AND LOGIC FUNCTIONS ---
def display_messages():
    """Displays the chat messages for the assessment."""
    if st.session_state.assessment_active and not st.session_state.assessment_messages:
        initial_message = "👋 Let's begin the **PHQ-9 screening**.<br><br>It's just 9 questions to help you understand your recent mood. Remember, this is not a diagnosis. Please answer based on how you've felt over the **last 2 weeks**."
        st.markdown(f"""<div style="display: flex; align-items: flex-start; justify-content: flex-start; margin-bottom: 1rem;"><img src="https://www.iconpacks.net/icons/2/free-robot-icon-2760-thumb.png" alt="Assistant" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 10px; margin-top: 5px;"><div style="background-color: #f0f2f6; color: #31333F; border-radius: 1rem; padding: 1rem; max-width: 80%; word-wrap: break-word; box-shadow: 0 4px 8px rgba(0,0,0,0.06);">{initial_message}</div></div>""", unsafe_allow_html=True)

    for msg in st.session_state.assessment_messages:
        if msg["role"] == "user":
            st.markdown(f"""<div style="display: flex; align-items: flex-start; justify-content: flex-end; margin-bottom: 1rem;"><div style="background-color: #0b93f6; color: white; border-radius: 1rem; padding: 1rem; max-width: 80%; word-wrap: break-word; box-shadow: 0 4px 8px rgba(0,0,0,0.06);">{msg['content']}</div><img src="https://img.icons8.com/?size=100&id=rrtYnzKMTlUr&format=png&color=000000" alt="User" style="width: 40px; height: 40px; border-radius: 50%; margin-left: 10px; margin-top: 5px;"></div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="display: flex; align-items: flex-start; justify-content: flex-start; margin-bottom: 1rem;"><img src="https://www.iconpacks.net/icons/2/free-robot-icon-2760-thumb.png" alt="Assistant" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 10px; margin-top: 5px;"><div style="background-color: #f0f2f6; color: #31333F; border-radius: 1rem; padding: 1rem; max-width: 80%; word-wrap: break-word; box-shadow: 0 4px 8px rgba(0,0,0,0.06);">{msg['content']}</div></div>""", unsafe_allow_html=True)

def run_assessment(model):
    """Manages the flow of asking the 9 PHQ questions."""
    questions = [
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
        "Trouble falling/staying asleep, or sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself or that you're a failure",
        "Trouble concentrating on things",
        "Moving/speaking slowly or being fidgety/restless",
        "Thoughts that you would be better off dead or hurting yourself"
    ]
    q_index = st.session_state.current_question

    if q_index < len(questions):
        current_q = questions[q_index]
        question_text = f"**Question {q_index + 1}/{len(questions)}:** Over the last 2 weeks, how often have you been bothered by... <br><br>> {current_q}"
        st.markdown(f"""<div style="display: flex; align-items: flex-start; justify-content: flex-start; margin-bottom: 1rem;"><img src="https://www.iconpacks.net/icons/2/free-robot-icon-2760-thumb.png" alt="Assistant" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 10px; margin-top: 5px;"><div style="background-color: #f0f2f6; color: #31333F; border-radius: 1rem; padding: 1rem; max-width: 80%; word-wrap: break-word; box-shadow: 0 4px 8px rgba(0,0,0,0.06);">{question_text}</div></div>""", unsafe_allow_html=True)
        
        options_map = {"Not at all (0)": 0, "Several days (1)": 1, "More than half the days (2)": 2, "Nearly every day (3)": 3}
        answer = st.radio("Select how often:", options=options_map.keys(), key=f"q_{q_index}", index=None, horizontal=True)

        if answer is not None:
            score = options_map[answer]
            store_answer(q_index, score, answer)
    else:
        show_results()

def store_answer(q_index, score, user_response):
    """Saves the user's answer to the session and database, then moves to the next question."""
    conv_id = st.session_state.assessment_conversation_id
    st.session_state.answers.append(score)
    
    user_msg_content = f"Q{q_index+1}: {user_response}"
    st.session_state.assessment_messages.append({"role": "user", "content": user_msg_content})
    add_message(conv_id, "user", user_msg_content)
    
    st.session_state.current_question += 1
    st.rerun()

def show_results():
    """Calculates the total score and displays the final feedback."""
    conv_id = st.session_state.assessment_conversation_id
    total_score = sum(st.session_state.answers)
    
    st.session_state.last_assessment_score = total_score
    severity, feedback_details = get_severity_and_feedback(total_score)
    
    final_feedback_content = f"## 📊 Assessment Complete\n\n**Your total PHQ-9 score is: {total_score}/27**\n\n**Interpretation:** {severity}\n\n---\n\n### Suggestions & Next Steps\n\n{feedback_details}\n\n---\n**Disclaimer:** I am an AI, not a medical professional. Please consult a healthcare provider for medical advice."
    
    st.session_state.assessment_messages.append({"role": "assistant", "content": final_feedback_content})
    add_message(conv_id, "assistant", final_feedback_content)
    
    st.session_state.assessment_active = False
    st.success("Assessment complete! You can now generate a schedule from the homepage.")
    st.balloons()
    st.rerun()

# --- MAIN PAGE FUNCTION ---
def assessment_page():
    """The main entry point for the assessment page."""
    show_sidebar()
    st.title("PHQ-9 Depression Screening")
    st.markdown("---")

    model = configure_gemini()
    initialize_assessment_session()

    # --- LOGIC TO LOAD or CREATE a conversation ---
    # If a conversation was selected from the sidebar, load its messages.
    if st.session_state.assessment_conversation_id and not st.session_state.assessment_messages:
        st.session_state.assessment_messages = get_messages(st.session_state.assessment_conversation_id)
        
    # If this is a NEW assessment (active is True but no ID), create a conversation ID for it with a numbered title.
    if st.session_state.assessment_active and st.session_state.assessment_conversation_id is None:
        # --- NEW NAMING LOGIC ---
        user_id = st.session_state.user_id
        # Get all existing conversations to determine the next number
        existing_conversations = get_user_conversations(user_id)
        # Count how many existing titles start with "PHQ-9 Assessment"
        assessment_count = sum(1 for conv in existing_conversations if conv['title'].startswith("PHQ-9 Assessment"))
        # Create the new title with the next number
        new_title = f"PHQ-9 Assessment #{assessment_count + 1}"
        
        st.session_state.assessment_conversation_id = create_conversation(user_id, title=new_title)
        # --- END OF NEW NAMING LOGIC ---
        
    # Display all messages
    display_messages()
    
    # Run the main logic
    if st.session_state.assessment_active:
        run_assessment(model)
    else:
        # This message shows when viewing a past assessment
        st.info("You are viewing a past assessment. To start a new one, go to Home.")
