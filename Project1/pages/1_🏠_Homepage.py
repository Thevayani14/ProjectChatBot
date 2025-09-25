import streamlit as st
import streamlit.components.v1 as components
from database import get_todays_events
from datetime import date
from styles import get_dark_mode_css
from sidebar import display_homepage_sidebar

# --- Page Configuration and Styling (Safe to run first) ---
st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.markdown(get_dark_mode_css(), unsafe_allow_html=True)
st.markdown("""<style>[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True)

# --- CRITICAL: Authentication Check (MUST be done before using user data) ---
if not st.session_state.get("logged_in"):
    st.error("Please log in to access this page.")
    st.switch_page("app.py")
    st.stop()  # Immediately stop the script if not logged in

# --- Now it is safe to display the sidebar and the rest of the page ---
display_homepage_sidebar()

def render_chatbot():
    """Renders the floating chatbot button and popup."""
    components.html("""
        <div class="chat-icon" onclick="toggleChat()">💬</div>
        <div id="chat-popup" class="chat-popup">
            <div id="chat-header">Mental Health Assistant</div>
            <div id="chat-content"></div>
            <div id="chat-buttons">
                <button onclick="sendPredefined('What is the PHQ-9 assessment?')">What is the PHQ-9?</button>
                <button onclick="sendPredefined('How does the Schedule Generator work?')">Schedule Generator Info</button>
                <button onclick="sendPredefined('What does the Behavior Tracker do?')">Behavior Tracker Info</button>
                <button onclick="sendPredefined('What is Emotion Analysis?')">Emotion Analysis Info</button>
                <button onclick="sendPredefined('How do Game Suggestions work?')">Game Suggestions Info</button>
            </div>
        </div>
        <style>
            .chat-icon{position:fixed;bottom:20px;right:30px;width:60px;height:60px;background-color:#0b93f6;color:white;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:30px;cursor:pointer;box-shadow:0 4px 8px rgba(0,0,0,0.2);z-index:1000;}
            .chat-popup{position:fixed;bottom:90px;right:30px;width:350px;max-height:500px;background-color:#2e2e2e;border-radius:15px;box-shadow:0 8px 16px rgba(0,0,0,0.3);display:none;flex-direction:column;z-index:1000;border:1px solid #444;}
            #chat-header{padding:15px;background-color:#333;color:white;font-weight:bold;font-size:18px;text-align:center;border-top-left-radius:15px;border-top-right-radius:15px;}
            #chat-content{padding:15px;height:250px;overflow-y:auto;background-color:#2a2a2a;color:#f0f0f0;}
            #chat-buttons{padding:10px;display:flex;flex-direction:column;gap:5px;}
            #chat-buttons button{padding:10px;background-color:#555;color:white;border:none;border-radius:5px;cursor:pointer;font-weight:bold;}
            #chat-buttons button:hover{background-color:#666;}
        </style>
        <script>
            function toggleChat(){const c=document.getElementById('chat-popup');c.style.display=c.style.display==='flex'?'none':'flex'}
            function sendPredefined(q){const r={"What is the PHQ-9 assessment?":"The PHQ-9 is a clinically validated questionnaire to screen for and measure the severity of depression.","How does the Schedule Generator work?":"It uses your latest assessment score and preferences to create a personalized weekly self-care plan to help you build healthy routines.","What does the Behavior Tracker do?":"It helps you log and monitor gaming habits like playtime and mood to find patterns that affect your well-being.","What is Emotion Analysis?":"This tool uses AI to analyze text you provide, helping you identify underlying emotions like joy, sadness, or anger for better self-awareness.","How do Game Suggestions work?":"It recommends games based on your mood, assessment results, and gaming habits to support your mental state, suggesting calming or engaging games as needed."};const d=document.getElementById('chat-content');d.innerHTML=`<div style='margin-bottom:10px;'><b>You:</b> ${q}</div><div><b>Bot:</b> ${r[q]}</div>`;d.scrollTop=d.scrollHeight}
        </script>
    """, height=600)

# --- Main Page Content ---
# This line will only be reached if the user is logged in and user_data exists.
display_name = st.session_state.user_data.get('username')

st.title(f"🏠 Welcome to Your Mental Health Companion, {display_name}")
st.markdown("Select one of the tools below to manage your mental well-being.")
st.markdown("---")
st.subheader("Your Tools")

def card_with_navigation(title, description, image_url, page_name):
    """Creates a clickable card that navigates to a specified page."""
    # Note: st.page_link creates the button, so wrapping the card in an <a> tag is redundant.
    # The container itself is not clickable, but the button inside it will work.
    with st.container(border=True, height=400):  # Increased height to fit content better
         st.markdown(
    f"""
    <div class="tool-card" style="
        padding: 20px; 
        text-align: center; 
        min-height: 240px; 
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    ">
        <div>
            <img src="{image_url}" width="80" style="margin-bottom: 10px;" />
            <h4 style="margin-top:20px; margin-bottom:15px;">{title}</h4>
            <p style="margin-bottom: 20px;">{description}</p>
        </div>
    </div>

    <style>
        div.tool-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 14px rgba(0,0,0,0.2);
            background-color: #303030;
            border-radius: 10px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

         st.page_link(page_name, label=f"Open {title.split(' ')[0]}", use_container_width=True)


# --- Tool Cards ---
# Row 1
col1, col2, col3 = st.columns(3)
with col1:
    card_with_navigation("PHQ-9 Assessment", "Take the PHQ-9 screening to check in with your emotional well-being.", "https://img.icons8.com/plasticine/100/test-tube.png", "pages/2_🧠_Assessment.py")
with col2:
    card_with_navigation("Schedule Generator", "Get a personalized weekly self-care plan for your calendar.", "https://img.icons8.com/plasticine/100/calendar.png", "pages/3_✍️_Schedule_Generator.py")
with col3:
    card_with_navigation("Full Calendar", "View your full schedule and add your own personal notes.", "https://img.icons8.com/?size=100&id=89550&format=png&color=40C057", "pages/4_📅_Calendar.py")

st.markdown("<br>", unsafe_allow_html=True) # Spacer

# Row 2
col4, col5, col6 = st.columns(3)
with col4:
    card_with_navigation("Behaviour Tracker", "Log and view your gaming patterns and their link to mental health.", "https://img.icons8.com/plasticine/100/controller.png", "pages/5_🎮_Behaviour_Tracker.py")
with col5:
    card_with_navigation("Emotion Analysis", "Analyze how you feel by interpreting emotional tones in your text.", "https://img.icons8.com/plasticine/100/brain.png", "pages/6_💬_Emotion_Analysis.py")
with col6:
    card_with_navigation("Game Suggestions", "Get personalized game recommendations based on your current state.", "https://img.icons8.com/plasticine/100/controller.png", "pages/7_🎯_Game_Suggestions.py")

render_chatbot()