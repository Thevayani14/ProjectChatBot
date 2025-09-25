# assessment.py (Corrected for IndentationError)

import streamlit as st
from database import (
    add_message, get_messages, get_user_conversations, create_conversation, 
    update_conversation_score, delete_conversation, update_conversation_video_url,
    update_conversation_answers,clear_all_assessments 
)
from shared import get_severity_and_feedback, display_progress_dashboard
from sidebar import display_sidebar

# --- Page Setup & Login Check ---
st.set_page_config(layout="wide", page_title="PHQ-9 Assessment")
if not st.session_state.get("logged_in"):
    st.error("Please log in to access this page.")
    st.switch_page("app.py")
    st.stop()

if 'confirming_clear_assessments' not in st.session_state:
    st.session_state.confirming_clear_assessments = False

# --- HELPER FUNCTIONS ---
def initialize_new_assessment():
    st.session_state.assessment_status = "in_progress"
    st.session_state.assessment_messages = []
    st.session_state.current_question = 0
    st.session_state.answers = []
    st.session_state.viewing_assessment = None
    if "assessment_result" in st.session_state:
        del st.session_state.assessment_result

def display_messages(messages):
    for msg in messages:
        if msg["role"] == "user":
            st.markdown(f"""<div style="display: flex; align-items: flex-start; justify-content: flex-end; margin-bottom: 1rem;"><div style="background-color: #0b93f6; color: white; border-radius: 1rem; padding: 1rem; max-width: 80%; word-wrap: break-word; box-shadow: 0 4px 8px rgba(0,0,0,0.06);">{msg['content']}</div><img src="https://img.icons8.com/?size=100&id=rrtYnzKMTlUr&format=png&color=000000" alt="User" style="width: 40px; height: 40px; border-radius: 50%; margin-left: 10px; margin-top: 5px;"></div>""", unsafe_allow_html=True)
        else: # Assistant
            with st.container():
                col1, col2 = st.columns([0.07, 0.93], gap="small")
                with col1:
                    st.image("https://www.iconpacks.net/icons/2/free-robot-icon-2760-thumb.png", width=40)
                with col2:
                    st.markdown(msg['content'], unsafe_allow_html=True)

def assessment_page():
    display_sidebar(page_name="assessment")

    if "viewing_assessment" not in st.session_state:
        st.session_state.viewing_assessment = None
    if st.session_state.viewing_assessment:
        view_past_assessment()
    else:
        run_new_assessment()

# --- UI DISPLAY FUNCTIONS ---
def view_past_assessment():
    st.title("Viewing Past Assessment")
    if st.button("⬅️ Start New Assessment"):
        initialize_new_assessment()
        st.rerun()
    messages = get_messages(st.session_state.viewing_assessment['id'])
    display_messages(messages)
    video_url = st.session_state.viewing_assessment.get("video_url")
    if video_url:
        st.video(video_url)

def display_completion_page():
    """Displays the final results and the new, interactive, personalized plan."""
    result = st.session_state.assessment_result
    st.balloons()

    with st.container(border=True):
        st.header("📊 Assessment Complete")
        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("Your PHQ-9 Score", f"{result['score']}/27")
        col2.metric("Interpretation", result['severity'])
        
    st.divider()
    
    feedback = result['feedback_dict']
    tab1, tab2 = st.tabs(["⭐ Overview & Resources", "📝 Your Personalized Plan"])

    with tab1:
        st.subheader("What Your Score Means")
        if "overview_html" in feedback:
            st.markdown(feedback["overview_html"], unsafe_allow_html=True)
        elif "overview" in feedback:
            st.info(feedback["overview"])
        
        if "video_url" in feedback:
            st.video(feedback["video_url"])
            st.caption("This video may offer helpful perspectives or techniques.")

    with tab2:
        st.subheader("A Plan Tailored To You")
        st.markdown("Based on your answers, here are some targeted strategies for the areas you're finding most challenging.")
        
        if not feedback.get("personalized_plan"):
            st.success("Your responses don't indicate any specific, recurring problem areas. Keep up the great work!")
        else:
            for i, suggestion in enumerate(feedback["personalized_plan"]):
                with st.container(border=True):
                    st.markdown(f"#### {suggestion['title']}")
                    st.write(suggestion['text'])
                    st.markdown(f"**{suggestion['exercise_title']}**")
                    st.text_area(
                        label="Your private thoughts go here. This is for your reflection and is not saved.",
                        value=suggestion['exercise_prompt'],
                        height=150,
                        key=f"exercise_{i}"
                    )
                st.markdown("---")
    
    st.divider()
    with st.container(border=True):
        st.subheader("See Your Journey Over Time")
        st.markdown("View your full progress dashboard to see how this assessment fits into your overall journey.")
        display_progress_dashboard(st.session_state.user_data['id'])
        
        st.markdown("") # Spacer
        col_a, col_b = st.columns(2)
        with col_a:
            st.page_link("pages/3_📈_My_Progress.py", label="Go to Full Dashboard 📈", use_container_width=True)
        with col_b:
            st.page_link("pages/3_✍️_Schedule_Generator.py", label="Create a Schedule Based on These Results ✍️", use_container_width=True)

    st.divider()
    if st.button("Take Another Assessment", use_container_width=True):
        initialize_new_assessment()
        st.rerun()
    
    st.caption("Disclaimer: This screening tool is not a substitute for a professional diagnosis. Please consult a healthcare provider for medical advice.")

# --- ASSESSMENT LOGIC (run_new_assessment is MODIFIED) ---
def run_new_assessment():
    st.title("PHQ-9 Mental Wellness Screening")
    
    if "assessment_status" not in st.session_state:
        initialize_new_assessment()
    if st.session_state.assessment_status == "completed":
        display_completion_page()
        return

    # These are the full question texts that match the `shared.py` keys
    questions = [
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
        "Trouble falling or staying asleep, or sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself - or that you are a failure or have let yourself or your family down",
        "Trouble concentrating on things, such as reading the newspaper or watching television",
        "Moving or speaking so slowly that other people could have noticed. Or the opposite - being so fidgety or restless that you have been moving around a lot more than usual",
        "Thoughts that you would be better off dead, or of hurting yourself"
    ]
    q_index = st.session_state.current_question

    if q_index < len(questions):
        with st.container(border=True):
            progress_value = (q_index) / len(questions)
            st.progress(progress_value, text=f"Question {q_index + 1} of {len(questions)}")
            st.markdown(f"##### Over the last 2 weeks, how often have you been bothered by:")
            st.subheader(f"*{questions[q_index]}*")
            options_map = {"Not at all": 0, "Several days": 1, "More than half the days": 2, "Nearly every day": 3}
            answer = st.radio("Select your answer:", options=options_map.keys(), key=f"q_{q_index}", index=None, horizontal=True, label_visibility="collapsed")
            if answer is not None:
                score = options_map[answer]
                st.session_state.answers.append(score)
                st.session_state.current_question += 1
                st.rerun()
    # --- INDENTATION FIX IS HERE ---
    # The 'else' block is now correctly aligned with the 'if' statement above.
    else:
        with st.spinner("Finalizing and saving your assessment..."):
            user_id = st.session_state.user_data['id']
            answers_array = st.session_state.answers
            total_score = sum(answers_array)

            # Correctly identify problem areas
            scored_questions = sorted(zip(answers_array, questions), key=lambda item: item[0], reverse=True)
            problem_areas = [q_text for score, q_text in scored_questions if score > 1][:3]

            # Get feedback, which now includes the video_url
            severity, feedback_dict = get_severity_and_feedback(total_score, problem_areas)
            video_url = feedback_dict.get("video_url")

            # Database saving logic
            all_conversations = get_user_conversations(user_id)
            assessment_count = sum(1 for conv in all_conversations if conv['title'].startswith("PHQ-9 Assessment"))
            new_title = f"PHQ-9 Assessment #{assessment_count + 1}"
            conv_id = create_conversation(user_id, title=new_title)
            
            update_conversation_answers(conv_id, answers_array)
            update_conversation_score(conv_id, total_score)
            
            if video_url:
                update_conversation_video_url(conv_id, video_url)
            
            # Message saving logic (can be simplified or removed if not displaying chat history)
            final_feedback_text = f"**Assessment Complete**\n- Score: {total_score}/27\n- Severity: {severity}"
            st.session_state.assessment_messages.append({"role": "assistant", "content": final_feedback_text})
            for msg in st.session_state.assessment_messages:
                add_message(conv_id, msg['role'], msg['content'])
            
            # Store results in session state
            st.session_state.assessment_result = {
                "score": total_score, 
                "severity": severity,  
                "feedback_dict": feedback_dict,
                "problem_areas": problem_areas
            }
            st.session_state.assessment_status = "completed"
            st.rerun()

# --- ENTRY POINT ---
assessment_page()