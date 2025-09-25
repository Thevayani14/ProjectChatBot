import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from sidebar import display_sidebar
#from sidebar import show_sidebar
from database import (
    save_behavior_log,
    get_behavior_logs,
    get_latest_phq9,
)

# Page guard
if not st.session_state.get("logged_in"):
    st.error("Please log in to access this page.")
    st.switch_page("app.py")
    st.stop()

def compute_weighted_risk(row, phq9_score=0):
    score = 0
    if row["hours_played"] > 6: score += 3
    elif row["hours_played"] > 4: score += 1
    if row["mood_score"] < -0.5: score += 4
    elif row["mood_score"] < 0: score += 2
    if row["solo_play_ratio"] > 0.8: score += 2
    if row["late_night_gaming"]: score += 1
    if row["physical_breaks"] < 1: score += 1
    if row["social_interaction_score"] < 3: score += 2
    if phq9_score > 19: score += 5
    elif phq9_score > 14: score += 4
    elif phq9_score > 9: score += 3
    elif phq9_score > 4: score += 1
    return min(score, 20)

def generate_holistic_insights(df, phq9):
    if df.empty or len(df) < 3:
        return {}
    insights = {}
    df['risk_trend'] = df['risk_score'].rolling(window=7, min_periods=1).mean().diff().fillna(0)
    df['mood_trend'] = df['mood_score'].rolling(window=7, min_periods=1).mean().diff().fillna(0)
    insights['recent_risk_trend'] = df['risk_trend'].iloc[-1]
    insights['recent_mood_trend'] = df['mood_trend'].iloc[-1]
    high_risk_days = df[df['risk_score'] > 10]
    if not high_risk_days.empty:
        contributors = {}
        if (high_risk_days['hours_played'] > 6).any():
            contributors['Excessive Playtime (>6 hrs)'] = (high_risk_days['hours_played'] > 6).sum()
        if (high_risk_days['mood_score'] < -0.5).any():
            contributors['Very Low Mood'] = (high_risk_days['mood_score'] < -0.5).sum()
        if (high_risk_days['solo_play_ratio'] > 0.8).any():
            contributors['High Ratio of Solo Play'] = (high_risk_days['solo_play_ratio'] > 0.8).sum()
        if (high_risk_days['late_night_gaming']).any():
            contributors['Late-Night Gaming'] = (high_risk_days['late_night_gaming']).sum()
        insights['top_risk_contributors'] = sorted(contributors.items(), key=lambda item: item[1], reverse=True)[:3]
    if len(df['solo_play_ratio'].unique()) > 1 and len(df['mood_score'].unique()) > 1:
        correlation = df['solo_play_ratio'].corr(df['mood_score'])
        if correlation < -0.4:
            insights['solo_mood_correlation'] = correlation
    insights['phq9_severity'] = phq9.get('severity_level', 'Unknown') if phq9 else 'Unknown'
    return insights

def generate_actionable_suggestions(insights):
    suggestions = []
    if insights.get('phq9_severity') in ["Moderately Severe", "Severe"]:
        suggestions.append(("🚨 **Prioritize Mental Health:** Significant distress detected. Please consider professional help.", "high"))
    elif insights.get('phq9_severity') == "Moderate":
        suggestions.append(("⚠️ **Monitor Your Mood:** Moderate symptoms detected. Stay alert to mood changes.", "medium"))
    if insights.get('recent_risk_trend', 0) > 0.5:
        suggestions.append(("📈 **Negative Trend Alert:** Your risk score is increasing. Consider reducing gaming time.", "high"))
    for contributor, _ in insights.get('top_risk_contributors', []):
        if 'Excessive Playtime' in contributor:
            suggestions.append(("⏰ **Manage Playtime:** Long gaming sessions detected. Try setting limits.", "medium"))
        if 'Very Low Mood' in contributor:
            suggestions.append(("❤️ **Address Low Mood:** Frequent low moods identified. Take breaks when feeling down.", "high"))
        if 'Solo Play' in contributor:
            suggestions.append(("🤝 **Connect with Others:** High solo play ratio detected. Try social gaming.", "low"))
    if 'solo_mood_correlation' in insights:
        suggestions.append(("📊 **Insight:** Solo play correlates with low mood. Social play is recommended.", "low"))
    if not suggestions:
        suggestions.append(("✅ **Maintaining Balance:** Your gaming habits appear healthy. Keep it up!", "green"))
    return suggestions

def behaviour_page():
    display_sidebar(page_name="behaviour")
    st.title("💡 Gaming Behaviour Tracking")

    user_id = st.session_state.user_data['id']

    st.markdown("### 🎮 Log Today’s Gaming Behavior")
    st.info("Fill in your habits for today to receive mental health insights. Your input is safe and only visible to you.")

    with st.form("behavior_form"):
        date = st.date_input("📅 Date", datetime.date.today())

        hours_played = st.selectbox("🎮 Hours played", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 24])

        mood_score_map = {
            "🙂 Very Good (+1)": 1.0,
            "😊 Good (+0.5)": 0.5,
            "😐 Neutral (0)": 0.0,
            "🙁 Bad (-0.5)": -0.5,
            "😞 Very Bad (-1)": -1.0,
        }
        mood_option = st.radio("🙂 How was your mood after gaming?", list(mood_score_map.keys()))
        mood_score = mood_score_map[mood_option]

        solo_option = st.radio(
            "🧑‍🤝‍🧑 Time spent playing solo?",
            ["0% (only multiplayer)", "25%", "50%", "75%", "100% (only solo)"]
        )
        solo_play_ratio = {
            "0% (only multiplayer)": 0.0,
            "25%": 0.25,
            "50%": 0.5,
            "75%": 0.75,
            "100% (only solo)": 1.0
        }[solo_option]

        late_night_gaming = st.checkbox("🌙 Played late at night (after 11 PM)")

        physical_breaks = st.selectbox("🚶 Physical breaks taken", list(range(0, 11)))

        social_score = st.selectbox("💬 Social interaction score (0 = none, 10 = very social)", list(range(0, 11)))

        submitted = st.form_submit_button("💾 Save & Generate Insights")

    phq9 = get_latest_phq9(user_id)
    phq9_score = phq9['total_score'] if phq9 else 0

    if submitted:
        save_behavior_log(
            user_id=user_id,
            date=date,
            hours_played=hours_played,
            mood_score=mood_score,
            solo_play_ratio=solo_play_ratio,
            late_night_gaming=late_night_gaming,
            physical_breaks=physical_breaks,
            social_interaction_score=social_score
        )
        st.success("✅ Behavior log saved!")

    df = get_behavior_logs(user_id)

    if df.empty:
        st.info("Log your first behavior to begin tracking your wellness journey.")
        return

    df_sorted = df.sort_values("date").reset_index(drop=True)
    df_sorted['risk_score'] = df_sorted.apply(lambda row: compute_weighted_risk(row, phq9_score), axis=1)

    insights = generate_holistic_insights(df_sorted, phq9)
    suggestions = generate_actionable_suggestions(insights)

    st.divider()
    st.header("🚀 Your Command Center")

    col1, col2 = st.columns(2)
    with col1:
        today_risk = df_sorted['risk_score'].iloc[-1]
        risk_color = "red" if today_risk > 15 else "orange" if today_risk > 10 else "green"
        st.plotly_chart(go.Figure(go.Indicator(
            mode="gauge+number", value=today_risk,
            title={'text': "Today's Risk Score"},
            number={'font': {'size': 40}},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [None, 20]}, 'bar': {'color': risk_color}}
        )).update_layout(height=250, margin={'t': 40, 'b': 40}), use_container_width=True)

    with col2:
        avg_mood = df_sorted['mood_score'].mean()
        mood_color = "green" if avg_mood > 0.3 else "orange" if avg_mood > -0.3 else "red"
        st.plotly_chart(go.Figure(go.Indicator(
            mode="gauge+number", value=avg_mood,
            title={'text': "Average Mood Score"},
            number={'font': {'size': 40}},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [-1, 1]}, 'bar': {'color': mood_color}}
        )).update_layout(height=250, margin={'t': 40, 'b': 40}), use_container_width=True)

    st.subheader("🎯 Your Personalized Action Plan")
    with st.container(border=True):
        for suggestion, priority in suggestions:
            if priority == "high": st.error(suggestion, icon="🚨")
            elif priority == "medium": st.warning(suggestion, icon="⚠️")
            elif priority == "low": st.info(suggestion, icon="💡")
            else: st.success(suggestion, icon="✅")

    with st.expander("🔬 View Deep Dive Analytics"):
        st.subheader("📈 Risk & Mood Trends Over Time")
        df_sorted['risk_score'] = pd.to_numeric(df_sorted['risk_score'], errors='coerce')
        df_sorted['mood_score'] = pd.to_numeric(df_sorted['mood_score'], errors='coerce')
        df_sorted['date'] = pd.to_datetime(df_sorted['date'], errors='coerce')

        fig_trends = px.line(df_sorted, x='date', y=['risk_score', 'mood_score'], title="Risk vs. Mood", markers=True)
        st.plotly_chart(fig_trends, use_container_width=True)

        st.subheader("📊 Top Risk Factors")
        if 'top_risk_contributors' in insights:
            contributors_df = pd.DataFrame(insights['top_risk_contributors'], columns=['Factor', 'Count'])
            fig_factors = px.bar(contributors_df, x='Count', y='Factor', orientation='h', title="Most Frequent Contributors to High-Risk Days")
            st.plotly_chart(fig_factors, use_container_width=True)
        else:
            st.info("No high-risk days detected yet. Keep up the good work!")

    with st.expander("📋 View Full Behavior Log"):
        st.dataframe(df_sorted.sort_values("date", ascending=False))

behaviour_page()
