import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sidebar import display_sidebar

# Make sure to import your custom modules
#from sidebar import show_sidebar
from database import create_conversation, save_emotion_log, get_emotion_history

# Page guard
if not st.session_state.get("logged_in"):
    st.error("Please log in to access this page.")
    st.switch_page("app.py")
    st.stop()

# --- CORE LOGIC (UNCHANGED) ---

@st.cache_resource
def download_vader():
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        nltk.download('vader_lexicon')

@st.cache_resource
def load_models():
    transformer_model_name = "bhadresh-savani/distilbert-base-uncased-emotion"
    tokenizer = AutoTokenizer.from_pretrained(transformer_model_name)
    transformer_model = AutoModelForSequenceClassification.from_pretrained(transformer_model_name)
    vader_analyzer = SentimentIntensityAnalyzer()
    return tokenizer, transformer_model, vader_analyzer

def predict_transformer_emotion(text, tokenizer, model):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    probs = torch.nn.functional.softmax(logits, dim=1)[0]
    labels = model.config.id2label
    return {labels[i]: float(probs[i]) for i in range(len(probs))}

def predict_vader_sentiment(text, analyzer):
    return analyzer.polarity_scores(text)

def highlight_emotion_keywords(text, emotion):
    emotion_keyword_map = {
        'sadness': ['sad', 'depressed', 'crying', 'lonely', 'unhappy', 'lost', 'empty'],
        'joy': ['happy', 'joyful', 'excited', 'amazing', 'great', 'love', 'fantastic'],
        'love': ['love', 'adore', 'heart', 'wonderful', 'beautiful'],
        'anger': ['angry', 'mad', 'furious', 'hate', 'rage', 'frustrated'],
        'fear': ['scared', 'fearful', 'terrified', 'anxious', 'nervous', 'afraid'],
        'surprise': ['surprised', 'shocked', 'wow', 'omg', 'unbelievable']
    }
    highlighted_parts = []
    words = text.split()
    for word in words:
        clean_word = word.lower().strip(".,!?")
        if clean_word in emotion_keyword_map.get(emotion, []):
            highlighted_parts.append(f"<span style='background-color: #FFD700; padding: 2px 5px; border-radius: 5px; font-weight: bold;'>{word}</span>")
        else:
            highlighted_parts.append(word)
    return " ".join(highlighted_parts)

def get_emotion_feedback(emotion, volatility_level=None):
    base_feedback = {
        'sadness': "It's okay to feel sad. This is a common human experience. Acknowledging this is a strong first step.",
        'joy': "Wonderful! Feeling joy is a sign of positive engagement. Embrace this feeling and reflect on what led to it.",
        'love': "Feeling love or affection is a powerful connector, central to building strong communities and friendships.",
        'anger': "Anger is a natural response to frustration. It's a signal that something needs attention. A short break can help you process this.",
        'fear': "Fear or anxiety is the body's natural alarm system. Grounding techniques, like focusing on your breathing, can be very effective.",
        'surprise': "Surprise indicates an unexpected event. It's an opportunity to adapt and learn."
    }
    feedback = base_feedback.get(emotion, "Reflecting on your emotions is a great step towards well-being.")
    
    if volatility_level == 'High':
        feedback += "\n\n**High Volatility Alert:** Your emotions have been shifting significantly. This can be draining. It might be helpful to focus on grounding activities or take a break to stabilize."
    elif volatility_level == 'Moderate':
        feedback += "\n\n**Moderate Volatility:** Your emotional state has seen some ups and downs. This is normal, but it's good to be aware of."

    return feedback

# --- NEW: COMPLEX FUNCTION FOR EMOTIONAL VOLATILITY ---
def calculate_emotional_volatility(history_df):
    """
    Calculates the emotional volatility based on the standard deviation of recent
    VADER compound scores.
    """
    if len(history_df) < 3:
        return 0, 'Low' # Not enough data for a meaningful calculation

    # Filter for the last 7 days of data
    seven_days_ago = pd.to_datetime('today') - pd.Timedelta(days=7)
    recent_history = history_df[history_df['date'] >= seven_days_ago]
    
    if len(recent_history) < 3:
        return 0, 'Low'

    # Calculate standard deviation of the VADER compound score
    volatility_std = recent_history['vader_compound'].std()

    # Normalize the score to a 0-100 scale (assuming max std dev is around 0.7 for VADER)
    normalized_volatility = min((volatility_std / 0.7) * 100, 100)

    # Determine volatility level
    if normalized_volatility >= 75:
        level = 'High'
    elif normalized_volatility >= 40:
        level = 'Moderate'
    else:
        level = 'Low'
        
    return normalized_volatility, level

# --- VISUAL FUNCTIONS ---
EMOTION_STYLES = {
    'joy': {'emoji': '😊', 'color': '#FFD700'}, 'sadness': {'emoji': '😢', 'color': '#5271FF'},
    'anger': {'emoji': '😠', 'color': '#FF4B4B'}, 'fear': {'emoji': '😨', 'color': '#AF52FF'},
    'love': {'emoji': '❤️', 'color': '#FF69B4'}, 'surprise': {'emoji': '😲', 'color': '#32CD32'},
}
DEFAULT_STYLE = {'emoji': '🤔', 'color': '#808080'}

def get_emotion_style(emotion):
    return EMOTION_STYLES.get(emotion, DEFAULT_STYLE)

def create_gauge_chart(value, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number={'suffix': "%", 'font': {'size': 40}},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20}},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': color, 'thickness': 0.3}}
    ))
    fig.update_layout(height=280, margin={'t': 50, 'b': 30, 'l': 30, 'r': 30}, paper_bgcolor="rgba(0,0,0,0)", font={'color': "#E0E0E0"})
    return fig

def create_vader_gauge_chart(compound_score):
    normalized_value = (compound_score + 1) / 2 * 100
    fig = go.Figure(go.Indicator(
        mode="gauge", value=normalized_value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "💬 VADER Sentiment Score", 'font': {'size': 20}},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#00BFFF", 'thickness': 0.3}}
    ))
    fig.add_annotation(x=0.5, y=0.35, text=f"{compound_score:.2f}", showarrow=False, font=dict(size=40, color="#E0E0E0"))
    fig.update_layout(height=280, margin={'t': 50, 'b': 30, 'l': 30, 'r': 30}, paper_bgcolor="rgba(0,0,0,0)", font={'color': "#E0E0E0"})
    return fig

# --- Main Emotion Detection Page ---
def emotion_page():
    download_vader()
    display_sidebar(page_name="emotion")
    tokenizer, transformer_model, vader_analyzer = load_models()
    
    # if "user_id" in st.session_state and "emotion_logged" not in st.session_state:
    #     create_conversation(st.session_state.user_id, title="Advanced Emotion Analysis")
    #     st.session_state.emotion_logged = True

    st.title("🧠 Gaming Chat Emotion Analysis")
    st.markdown("Dive deep into the emotions of your gaming chats to foster better mental health.")
    
    user_id = st.session_state.user_data['id']
    user_input = st.text_area("💬 Enter a gaming chat message or describe how you're feeling:", height=150)

    if st.button("🔍 Analyze and Understand My Emotion"):
        if not user_input.strip():
            st.warning("⚠️ Please enter a message to analyze.")
            return

        # --- Primary Analysis ---
        transformer_scores = predict_transformer_emotion(user_input, tokenizer, transformer_model)
        vader_scores = predict_vader_sentiment(user_input, vader_analyzer)
        df = pd.DataFrame(list(transformer_scores.items()), columns=["Emotion", "Probability"])
        df_sorted = df.sort_values(by="Probability", ascending=False).reset_index(drop=True)
        top_emotion_label = df_sorted.iloc[0]['Emotion']
        top_emotion_score = float(df_sorted.iloc[0]['Probability'])

        # --- NEW: Volatility Analysis ---
        emotion_history = get_emotion_history(st.session_state.get("user_id"))
        volatility_score, volatility_level = (0, 'Low')
        if emotion_history:
            history_df = pd.DataFrame(emotion_history)
            history_df['date'] = pd.to_datetime(history_df['date'])
            volatility_score, volatility_level = calculate_emotional_volatility(history_df)
        
        # --- Results Display ---
        st.header("Emotional Analysis Results")

        col1, col2, col3 = st.columns(3)
        with col1:
            style = get_emotion_style(top_emotion_label)
            st.plotly_chart(create_gauge_chart(
                top_emotion_score * 100, f"{style['emoji']} Dominant Emotion: {top_emotion_label.title()}", style['color']
            ), use_container_width=True)
        
        with col2:
            st.plotly_chart(create_vader_gauge_chart(vader_scores['compound']), use_container_width=True)
        
        with col3:
            volatility_color = 'red' if volatility_level == 'High' else 'yellow' if volatility_level == 'Moderate' else 'green'
            st.plotly_chart(create_gauge_chart(
                volatility_score, f"⚡ Emotional Volatility", volatility_color
            ), use_container_width=True)

        # --- Explanation Section ---
        with st.expander("How are these scores calculated?"):
            st.markdown("""
            **Dominant Emotion Score:** Comes from a Transformer AI model that reads your full sentence. It shows the AI's confidence in its choice of the primary emotion.
            
            **VADER Sentiment Score:** Calculated by the VADER tool, which is specialized for chat language. It ranges from -1.0 (most negative) to +1.0 (most positive). A score near 0.00 is neutral.
            
            **Emotional Volatility:** This new score measures the stability of your emotions over the last 7 days. It is calculated using the **standard deviation** of your VADER sentiment scores. A high score indicates large and frequent emotional swings.
            """)

        st.markdown("---")
        st.subheader("💡 Personal Feedback & Resources")
        st.info(get_emotion_feedback(top_emotion_label, volatility_level))
        st.markdown("---")
        
        # --- Other Details ---
        st.subheader("💬 Keywords in Your Message")
        st.markdown(highlight_emotion_keywords(user_input, top_emotion_label), unsafe_allow_html=True)
        
        st.subheader("📊 Detailed Emotion Distribution")
        bar_fig = px.bar(df_sorted, x="Probability", y="Emotion", orientation='h', color="Emotion",
                         color_discrete_map={e: s['color'] for e, s in EMOTION_STYLES.items()})
        st.plotly_chart(bar_fig, use_container_width=True)

        if user_id:
            save_emotion_log(
                user_id=user_id, date=datetime.date.today(),
                emotion=top_emotion_label, probability=top_emotion_score,
                vader_compound=vader_scores['compound']
            )
            st.success(f"✅ Your emotion analysis for **{top_emotion_label.title()}** has been logged.")

    if user_id:
        st.markdown("---")
        st.header("📈 Your Emotional Journey Over Time")
        try:
            emotion_history = get_emotion_history(user_id)
            if emotion_history:
                history_df = pd.DataFrame(emotion_history)
                history_df['date'] = pd.to_datetime(history_df['date'])
                
                color_map = {e: s['color'] for e, s in EMOTION_STYLES.items()}
                fig_hist = px.scatter(
                    history_df, x='date', y='vader_compound', color='emotion',
                    size='probability', hover_name='emotion', color_discrete_map=color_map,
                    title="Historical Emotion Trends"
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("No past emotion data found. Analyze a message to start tracking your emotional journey!")
        except Exception as e:
            st.error(f"Could not load emotion history. Error: {e}")

emotion_page()