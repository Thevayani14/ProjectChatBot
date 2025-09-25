import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
from dateutil.relativedelta import relativedelta
from database import get_scores_over_time 
import textwrap

def get_severity_and_feedback(total_score, problem_areas=[]):
    """
    Returns a dictionary with detailed feedback, including a relevant video link
    based on the user's score and specific problem areas.
    """
    
    # This dictionary of micro-suggestions for problem areas remains the same.
    micro_suggestions = {
        "Little interest or pleasure in doing things": {
            "title": "💡 Tip for Low Interest: Behavioral Activation",
            "text": "Sometimes, action has to come before motivation. This technique, called Behavioral Activation, is about doing small, manageable activities even when you don't feel like it. The act itself can help lift your mood and build momentum.",
            "exercise_title": "Guided Exercise: Your Next Small Step",
            "exercise_prompt": "What is one small, very low-effort activity you could do in the next hour? (e.g., listen to one favorite song, step outside for 60 seconds, stretch for 2 minutes, text a friend 'hi')."
        },
        "Feeling down, depressed, or hopeless": {
            "title": "❤️ Tip for Feeling Down: Self-Compassion",
            "text": "It's difficult to feel this way, and it's important to treat yourself with the same kindness you'd offer a friend. Acknowledge that this is a tough moment without judgment.",
            "exercise_title": "Guided Exercise: A Moment of Kindness",
            "exercise_prompt": "Write one kind, encouraging sentence to yourself as if you were talking to a friend who felt this way."
        },
         "Feeling bad about yourself - or that you are a failure or have let yourself or your family down": {
            "title": "🧠 Tip for Self-Criticism: Challenge Your Thoughts (CBT)",
            "text": "Our minds can get stuck in negative loops. A core technique of CBT is to question these automatic negative thoughts instead of accepting them as fact.",
            "exercise_title": "Guided Exercise: Mini Thought Record",
            "exercise_prompt": "1. What is the specific negative thought? \n2. What is one piece of evidence that this thought might not be 100% true? \n3. What is a more balanced or compassionate way to see the situation?"
        },
        # You can add more micro-suggestions here for other problems
    }

    # --- ENHANCED: Base feedback now includes specific video URLs ---
    if total_score <= 4:
        severity = "Minimal"
        feedback = {
            "overview": "Your responses suggest you're managing well. Continue to prioritize the activities that support your mental well-being. A great way to maintain this is through simple, regular mindfulness.",
            # --- VIDEO LINK ADDED ---
            "video_url": "https://www.youtube.com/watch?v=ZidGozDhOjg"  # 5-Min Mindfulness Meditation
        }
    elif 5 <= total_score <= 9:
        severity = "Mild"
        feedback = {
            "overview": "Your score suggests some mild down days. This is a great time to be proactive with self-care. Understanding the science behind well-being can be empowering.",
            # --- VIDEO LINK ADDED ---
            "video_url": "https://www.youtube.com/watch?v=4zsl1Bep1as"  # The Science of Well-Being (Yale)
        }
    elif 10 <= total_score <= 14:
        severity = "Moderate"
        feedback = {
            "overview": "Your responses indicate you've been feeling down more often than not. Learning to challenge negative thought patterns is a powerful skill. This video explains a core CBT technique called a 'Thought Record'.",
            # --- VIDEO LINK ADDED ---
            "video_url": "https://www.youtube.com/watch?v=Ve22zbqhxWY"  # "Thought Records" CBT Technique
        }
    elif 15 <= total_score <= 19:
        severity = "Moderately Severe"
        feedback = {
            "overview": "Your score suggests you're going through a very difficult time. It's important to seek support, and you don't have to do this alone. Guided meditation can be a helpful tool for finding calm when things feel overwhelming.",
            # --- VIDEO LINK ADDED ---
            "video_url": "https://www.youtube.com/watch?v=O-6f5wQXSu8"  # Guided Meditation for Depression
        }
    else: # 20 <= total_score <= 27
        severity = "Severe"
        # --- NO VIDEO HERE --- The focus is solely on immediate crisis support.
        feedback = {
            "overview_html": textwrap.dedent("""
                <div style="border: 2px solid #FF4B4B; border-radius: 10px; padding: 1rem; background-color: #FFF0F0;">
                    <h3 style="color: #D32F2F;">A Gentle Check-In... Your Well-being is the Priority</h3>
                    <p>Your answers suggest you are going through a particularly tough time. The most important thing is your safety.</p>
                    <p><strong>You are not alone, and immediate help is available. Please connect with someone right away:</strong></p>
                    <ul>
                        <li><strong>Talk or Text:</strong> Call or text <b>03 7627 2929 </b> The Malaysian Mental Health Association (MMHA), confidential conversation.</li>
                        <li><strong>Medical Support:</strong> Contact a doctor, therapist, or visit an urgent care facility.</li>
                    </ul>
                    <p>Taking this step is a sign of strength. Please prioritize your safety.</p>
                </div>
                """)
        }

    # This part for personalized text plans remains the same
    personalized_plan = []
    for area in problem_areas:
        if area in micro_suggestions and micro_suggestions[area]:
            personalized_plan.append(micro_suggestions[area])

    feedback["personalized_plan"] = personalized_plan
    return severity, feedback

def get_severity_for_score(score):
    """Returns only the severity string for a given score."""
    if score is None:
        return "N/A"
    if score <= 4: return "Minimal"
    if 5 <= score <= 9: return "Mild"
    if 10 <= score <= 14: return "Moderate"
    if 15 <= score <= 19: return "Moderately Severe"
    return "Severe"

def create_progress_chart(df):
    """Creates an interactive Plotly chart with severity bands."""
    fig = go.Figure()
    fig.add_hrect(y0=0, y1=4, line_width=0, fillcolor="green", opacity=0.1, annotation_text="Minimal", annotation_position="top left")
    fig.add_hrect(y0=5, y1=9, line_width=0, fillcolor="yellow", opacity=0.1, annotation_text="Mild", annotation_position="top left")
    fig.add_hrect(y0=10, y1=14, line_width=0, fillcolor="orange", opacity=0.1, annotation_text="Moderate", annotation_position="top left")
    fig.add_hrect(y0=15, y1=19, line_width=0, fillcolor="red", opacity=0.1, annotation_text="Moderately Severe", annotation_position="top left")
    fig.add_hrect(y0=20, y1=27, line_width=0, fillcolor="purple", opacity=0.1, annotation_text="Severe", annotation_position="top left")
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Score'], mode='lines+markers', name='Your Score', line=dict(color='#0b93f6', width=3), marker=dict(size=8)))
    fig.update_layout(title="Your PHQ-9 Journey", xaxis_title="Date of Assessment", yaxis_title="PHQ-9 Score", yaxis=dict(range=[-1, 28]), showlegend=False, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    return fig

def display_progress_dashboard(user_id):
    """A self-contained, reusable component to display the full wellness dashboard, now with detailed answers."""
    
    # --- Data Fetching (uses the updated DB function) ---
    score_data = get_scores_over_time(user_id)
    if 'Date' not in score_data.columns or score_data.empty:
        st.info("Your Wellness Dashboard will appear here once you complete your first assessment.")
        return # Exit the function if there's no data

    # --- Date Filter Section ---
    st.subheader("Filter Your View")
    today = datetime.date.today()
    col1, col2, col3 = st.columns(3)

    with col1:
        time_period = st.selectbox(
            "Select Period",
            ("All Time", "Last 90 Days", "Last 30 Days", "Custom Range"),
            key="time_filter_component"
        )

    # Filtering logic
    if time_period == "Last 30 Days":
        start_date = today - relativedelta(days=30)
        filtered_data = score_data[score_data['Date'] >= start_date]
    elif time_period == "Last 90 Days":
        start_date = today - relativedelta(days=90)
        filtered_data = score_data[score_data['Date'] >= start_date]
    elif time_period == "Custom Range":
        with col2:
            custom_start = st.date_input("Start Date", score_data['Date'].min(), key="custom_start_component")
        with col3:
            custom_end = st.date_input("End Date", today, key="custom_end_component")
        if custom_start and custom_end and custom_start <= custom_end:
            custom_start_date = custom_start if isinstance(custom_start, datetime.date) else custom_start
            custom_end_date = custom_end if isinstance(custom_end, datetime.date) else custom_end
            filtered_data = score_data[(score_data['Date'] >= custom_start_date) & (score_data['Date'] <= custom_end_date)]
        else:
            st.error("Error: Start date must be before end date.")
            filtered_data = pd.DataFrame() 
    else: # "All Time"
        filtered_data = score_data

    st.divider()

    # --- Main Dashboard Display ---
    if filtered_data.empty:
        st.warning(f"No assessment data found for '{time_period}'. Please adjust the filter.")
        return 

    # Display metrics and chart only if there's data
    if len(filtered_data) >= 2:
        st.header("At a Glance")
        latest_score = filtered_data['Score'].iloc[-1]
        previous_score = filtered_data['Score'].iloc[-2]
        average_score = round(filtered_data['Score'].mean(), 1)
        change = latest_score - previous_score
        trend_icon = "→"
        if change > 0: trend_icon = "↗" 
        if change < 0: trend_icon = "↘"
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Latest Score", f"{latest_score} ({get_severity_for_score(latest_score)})")
        m_col2.metric("Change Since Last", f"{abs(change)} Points", delta=f"{trend_icon} {change}", delta_color="inverse")
        m_col3.metric("Average Score (in period)", f"{average_score}")
        st.divider()

    st.header("Progress Over Time")
    chart = create_progress_chart(filtered_data)
    st.plotly_chart(chart, use_container_width=True)

    st.header("Detailed Assessment Breakdown")
    st.markdown("See your specific answers (0-3) for each question to understand what's driving your score.")
    
    # Take the last 5 rows for the breakdown, or fewer if not available
    recent_data = filtered_data.tail(5)
    
    if 'Answers' in recent_data.columns and not recent_data['Answers'].isnull().all():
        # Define short names for PHQ-9 questions
        q_short_names = {
            0: "Q1: Interest", 1: "Q2: Mood", 2: "Q3: Sleep",
            3: "Q4: Energy", 4: "Q5: Appetite", 5: "Q6: Self-Esteem",
            6: "Q7: Concentration", 7: "Q8: Agitation", 8: "Q9: Self-Harm"
        }
        
        # Expand the 'Answers' list into separate columns
        answers_df = pd.DataFrame(recent_data['Answers'].tolist(), index=recent_data.index)
        
        # Ensure we don't have more columns than we have names for
        num_cols_to_rename = min(len(q_short_names), answers_df.shape[1])
        answers_df = answers_df.iloc[:, :num_cols_to_rename] # Select only the valid columns
        answers_df.columns = [q_short_names[i] for i in range(num_cols_to_rename)]

        # Combine with Date and Score for the final display
        breakdown_df = pd.concat([recent_data[['Date', 'Score']].reset_index(drop=True), answers_df.reset_index(drop=True)], axis=1)
        
        st.dataframe(breakdown_df.set_index("Date"), use_container_width=True)
    else:
        st.info("No detailed answer data available for this period.")