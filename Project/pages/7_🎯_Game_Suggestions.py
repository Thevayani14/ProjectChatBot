import streamlit as st
#from sidebar import show_sidebar
from database import (
    get_latest_phq9,
    get_latest_emotion,
    get_behavior_logs,
    create_conversation
)
from sidebar import display_sidebar

# Page guard
if not st.session_state.get("logged_in"):
    st.error("Please log in to access this page.")
    st.switch_page("app.py")
    st.stop()

##CHANGED##
st.set_page_config(page_title="AI Suggestions", layout="wide")

if not st.session_state.get("logged_in"):
    st.error("Please log in to access this page.")
    st.switch_page("app.py")
    st.stop()
################################################################

# --- Game Details Database (with Mobile Games Added) ---
GAME_DETAILS = {
    # PC & Console Games
    "Stardew Valley": {
        "description": "A relaxing farming sim where you build a farm, raise animals, and befriend locals. Praised for its open-ended, stress-free gameplay.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/413150/header.jpg",
        "store_url": "https://store.steampowered.com/app/413150/Stardew_Valley/"
    },
    "Spiritfarer": {
        "description": "A cozy management game about dying. Build a boat to explore, care for spirits, and guide them to the afterlife in this beautiful, emotional adventure.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/972660/header.jpg",
        "store_url": "https://store.steampowered.com/app/972660/Spiritfarer_Farewell_Edition/"
    },
    "Animal Crossing": {
        "description": "Live a peaceful life in a village of charming animals. Enjoy fishing, bug catching, and decorating your home in this delightful social simulation.",
        "image_url": "https://assets.nintendo.com/image/upload/ar_16:9,c_lpad,w_1240/b_white/f_auto/q_auto/ncom/software/switch/70010000027619/9989372f4478142213d3955a43d0a64758e5c1516e05391c5d95f6164a2d1d4d.jpg",
        "store_url": "https://www.nintendo.com/store/products/animal-crossing-new-horizons-switch/"
    },
    "Slime Rancher": {
        "description": "A charming, first-person sandbox experience. Play as a young rancher who sets out to collect and raise slimes.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/433340/header.jpg",
        "store_url": "https://store.steampowered.com/app/433340/Slime_Rancher/"
    },
    "Unpacking": {
        "description": "A zen puzzle game about pulling possessions out of boxes and fitting them into a new home. A meditative story told through item placement.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1135690/header.jpg",
        "store_url": "https://store.steampowered.com/app/1135690/Unpacking/"
    },
    "Kind Words": {
        "description": "A game about writing nice letters to real people. Write and receive encouraging letters in a cozy room.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1070350/header.jpg",
        "store_url": "https://store.steampowered.com/app/1070350/Kind_Words_lo_fi_chill_beats_to_write_to/"
    },
    "Journey": {
        "description": "An anonymous online adventure where you explore a vast, ancient world. Soar above ruins and glide across sands to discover its secrets.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/638230/header.jpg",
        "store_url": "https://store.steampowered.com/app/638230/Journey/"
    },
    "The Sims 4": {
        "description": "A life simulation game where you create and control people. Customize Sims, build them the perfect home, and pursue their dreams.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1222670/header.jpg",
        "store_url": "https://store.steampowered.com/app/1222670/The_Sims_4/"
    },
    "Minecraft": {
        "description": "A game about placing blocks and going on adventures. Explore worlds and build amazing things from homes to castles.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/2050980/header.jpg",
        "store_url": "https://www.minecraft.net/en-us/store/minecraft-java-bedrock-edition-pc"
    },
    "Overcooked": {
        "description": "A chaotic cooperative cooking game. Working as a team, you must prepare, cook, and serve a variety of tasty orders.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/448510/header.jpg",
        "store_url": "https://store.steampowered.com/app/448510/Overcooked/"
    },
    "Hades": {
        "description": "A god-like rogue-like dungeon crawler. Wield the powers of Olympus to break free from the god of the dead.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1145360/header.jpg",
        "store_url": "https://store.steampowered.com/app/1145360/Hades/"
    },
    "Firewatch": {
        "description": "A single-player mystery in the Wyoming wilderness. Your only connection is the person on the other end of a radio.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/383870/header.jpg",
        "store_url": "https://store.steampowered.com/app/383870/Firewatch/"
    },
    "A Short Hike": {
        "description": "Hike, climb, and soar through the peaceful mountainside landscapes of Hawk Peak Provincial Park on your way to the summit.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1055540/header.jpg",
        "store_url": "https://store.steampowered.com/app/1055540/A_Short_Hike/"
    },
    "It Takes Two": {
        "description": "Embark on a crazy journey in this co-op platform adventure. Play as a clashing couple who must work together.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1426210/header.jpg",
        "store_url": "https://store.steampowered.com/app/1426210/It_Takes_Two/"
    },
    "Dorfromantik": {
        "description": "A peaceful building strategy and puzzle game where you create a beautiful village landscape by placing tiles.",
        "image_url": "https://cdn.akamai.steamstatic.com/steam/apps/1455840/header.jpg",
        "store_url": "https://store.steampowered.com/app/1455840/Dorfromantik/"
    },
    "Zelda BOTW": {
        "description": "Explore the wilds of Hyrule any way you like in this massive open-world adventure. A landmark game of exploration and discovery.",
        "image_url": "https://assets.nintendo.com/image/upload/ar_16:9,c_lpad,w_1240/b_white/f_auto/q_auto/ncom/software/switch/70010000000025/c42553b4fd0312c31e70ec74550474b9679e0a5a6764b423783c4bcd91136b22.jpg",
        "store_url": "https://www.nintendo.com/store/products/the-legend-of-zelda-breath-of-the-wild-switch/"
    },
    "Valorant": {
        "description": "A 5v5 character-based tactical shooter. Use sharp gunplay and tactical abilities on a global, competitive stage.",
        "image_url": "https://images.prismic.io/play-valorant/5899322a-3642-4993-8f03-625895e63073_VALORANT_PLAY_BUTTON_IMAGE_450x450.jpg",
        "store_url": "https://playvalorant.com/"
    },
    
    # --- MOBILE GAMES ADDED HERE ---
    "Monument Valley 2": {
        "description": "Guide a mother and her child as they embark on a journey through magical architecture and delightful puzzles.",
        "image_url": "https://media.pocketgamer.biz/images/130336/85136/monument-valley-2-is-now-available-on-netflix_l1200.jpg",
        "store_url": "https://www.monumentvalleygame.com/mv2"
    },
    "Alto's Odyssey": {
        "description": "Join Alto and his friends and soar above the dunes in a serene and endless sandboarding journey.",
        "image_url": "https://www.androidauthority.com/wp-content/uploads/2016/12/altos-odyssey.jpg",
        "store_url": "https://www.altosodyssey.com/"
    },
    "Sky: Children of the Light": {
        "description": "A peaceful, award-winning social adventure. Explore a beautifully-animated kingdom with other players.",
        "image_url": "https://play-lh.googleusercontent.com/HLMPD3jqB-PJoXKR2MihVdNV2FyWf2zYFuivhWwu7P-ecsjKiiNpwoWiVTg65b4ikw=w526-h296-rw",
        "store_url": "https://www.thatskygame.com/"
    },
    "Pokemon Go": {
        "description": "Explore the real world to catch Pokémon and complete challenges. A great way to turn a walk into an adventure.",
        "image_url": "https://pokemongo.com/img/posts/kantocelebration.jpg",
        "store_url": "https://pokemongolive.com/"
    },
}


# --- Helper Function ---
def get_game_details(game_name):
    return GAME_DETAILS.get(game_name)


# --- Game Suggestion Logic (Enhanced with Mobile Games) ---
def generate_game_suggestions(phq9, emotion, behavior_df):
    if behavior_df.empty:
        return {"error": "⚠️ No behavior logs found. Please submit your gaming behavior first."}

    latest = behavior_df.iloc[0]
    hours = latest.get('hours_played', 0)
    solo_ratio = latest.get('solo_play_ratio', 0)
    breaks = latest.get('physical_breaks', 2) # Default to a healthy number if not found
    late_night = latest.get('late_night_gaming', False)
    
    mood = emotion['emotion'] if emotion else "Neutral"
    phq9_score = phq9['total_score'] if phq9 else 0
    phq9_severity = phq9['severity_level'] if phq9 else "Unknown"

    suggestions = []

    # ✅ PHQ-9 Based
    if phq9_score >= 20 or phq9_severity == "Severe":
        suggestions.append({
            "title": "🧘 Relaxing & Healing Games",
            "reason": f"Your PHQ-9 shows **{phq9_severity} Depression**. It's important to focus on games that offer comfort and relaxation.",
            "games": ["Spiritfarer", "Kind Words", "Stardew Valley"]
        })
    elif phq9_score >= 15:
        suggestions.append({
            "title": "🌸 Gentle, Non-Stressful Games",
            "reason": f"**{phq9_severity} symptoms** detected. Look for creative, no-fail environments.",
            "games": ["Unpacking", "Slime Rancher", "Journey", "Monument Valley 2"]
        })
    elif phq9_score >= 10:
        suggestions.append({
            "title": "💙 Creative Sandboxes & Sim Games",
            "reason": f"**{phq9_severity} Depression** detected. Creative and low-pressure games can help.",
            "games": ["The Sims 4", "Minecraft", "Stardew Valley", "Dorfromantik"]
        })
    elif phq9_score >= 5:
        suggestions.append({
            "title": "🌿 Mild Stress Relievers",
            "reason": f"**{phq9_severity} symptoms.** Look for joyful, low-pressure games.",
            "games": ["Animal Crossing", "Overcooked", "A Short Hike", "Alto's Odyssey"]
        })
    else:
        suggestions.append({
            "title": "🚀 Challenge or Explore Freely",
            "reason": "Your PHQ-9 looks stable. Feel free to enjoy immersive adventures or competitive games based on your preference.",
            "games": ["Zelda BOTW", "Valorant", "Hades", "It Takes Two"]
        })

    # ✅ Emotion Based
    mood_lower = mood.lower()
    if mood_lower in ["sad", "down", "melancholy"]:
        suggestions.append({
            "title": "💙 Cozy, Comforting Games",
            "reason": "Feeling sad? Try these games that are known to uplift and soothe.",
            "games": ["Spiritfarer", "Unpacking", "A Short Hike"]
        })
    elif mood_lower in ["angry", "frustrated"]:
        suggestions.append({
            "title": "🔥 Energy Release Games",
            "reason": "Feeling angry? Play these action-heavy games for a cathartic release.",
            "games": ["Hades", "Valorant"]
        })
    elif mood_lower in ["fear", "anxious", "stressed"]:
        suggestions.append({
            "title": "🧘 Stress Reduction Games",
            "reason": "Feeling anxious? Calming, no-fail exploration can help.",
            "games": ["Journey", "Dorfromantik", "Alto's Odyssey", "Sky: Children of the Light"]
        })

    # ✅ Behavior Based
    if solo_ratio > 0.75:
        suggestions.append({
            "title": "🤝 High Solo Play Detected",
            "reason": "You've been playing mostly solo. Try these team-based games to foster social connection.",
            "games": ["Overcooked", "It Takes Two", "Sky: Children of the Light"]
        })
    if late_night:
        suggestions.append({
            "title": "🌙 Frequent Late-Night Gaming",
            "reason": "You're gaming late frequently. Try calming, short-session games before bed.",
            "games": ["Dorfromantik", "A Short Hike", "Monument Valley 2"]
        })
    if hours > 6:
        suggestions.append({
            "title": "⏰ Long Gaming Sessions Detected",
            "reason": "Balance is key. Try these shorter, satisfying story-driven experiences.",
            "games": ["Firewatch", "A Short Hike", "Journey"]
        })
    if breaks <= 1:
        suggestions.append({
            "title": "🏃 Low Physical Breaks Detected",
            "reason": "Remember to take care of your body! Try games that encourage real-world activity.",
            "games": ["Pokemon Go"]
        })

    if not suggestions:
        return {"message": "👍 Your gaming and mental health patterns look balanced! Play whatever brings you joy!"}
    return {"suggestions": suggestions}


# --- Main Suggestion Page ---
def suggestion_page():
    display_sidebar(page_name="suggestion")
    st.title("🎯 Game Suggestions for Your Well-Being")
    st.markdown("Here are personalized game recommendations based on your recent mood, PHQ-9 assessment, and gaming habits.")

    # if "user_id" not in st.session_state:
    #     st.error("❌ Please login to access game suggestions.")
    #     return

    # if "suggestion_logged" not in st.session_state:
    #     create_conversation(st.session_state.user_id, title="Game Suggestion")
    #     st.session_state.suggestion_logged = True

        # --- THIS IS THE FIX ---
    # 1. Get the user's ID from the 'user_data' dictionary that was set at login.
    user_id = st.session_state.user_data['id']
    # --- END OF FIX ---

    # if "suggestion_logged" not in st.session_state:
    #     # 2. Use the local variable 'user_id' for your database calls.
    #     create_conversation(user_id, title="Game Suggestion")
    #     st.session_state.suggestion_logged = True
        
     # 3. Use 'user_id' for all subsequent database calls as well.
    phq9 = get_latest_phq9(user_id)
    emotion = get_latest_emotion(user_id)
    behavior_df = get_behavior_logs(user_id)
    ###END OF FIX####


    
    with st.expander("Show My Current Mental Health & Behavior Snapshot"):
        col1, col2 = st.columns(2)
        with col1:
            if phq9:
                st.info(f"**PHQ-9 Severity:** {phq9['severity_level']}\n\n**Score:** {phq9['total_score']} / 27")
            else:
                st.warning("No PHQ-9 data found.")
        with col2:
            if emotion:
                st.info(f"**Last Detected Emotion:** {emotion['emotion']}")
            else:
                st.warning("No emotion data detected.")
        
        if behavior_df.empty:
            st.warning("No behavior data logged yet.")
        else:
            st.write("##### Latest Gaming Behavior:")
            st.dataframe(behavior_df.head(1))

    st.header("🎮 Here Are Your Recommended Games")

    result = generate_game_suggestions(phq9, emotion, behavior_df)

    if "error" in result:
        st.error(result["error"])
    elif "message" in result:
        st.success(result["message"])
    elif "suggestions" in result:
        displayed_games = set()
        for category in result["suggestions"]:
            # Check for new games in this category that haven't been shown yet
            new_games_to_show = [game for game in category["games"] if game not in displayed_games and game in GAME_DETAILS]
            if not new_games_to_show:
                continue

            st.subheader(category["title"], divider='rainbow')
            st.markdown(f"*{category['reason']}*")
            st.markdown("")

            for game_name in new_games_to_show:
                details = get_game_details(game_name)
                if details:
                    with st.container(border=True):
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.image(details["image_url"])
                        with col2:
                            st.markdown(f"#### {game_name}")
                            st.write(details["description"])
                            st.link_button("View on Store for Details & Trailer", details["store_url"], use_container_width=True)
                    
                    displayed_games.add(game_name)
            st.markdown("<br>", unsafe_allow_html=True)

    st.info("💡 These suggestions are for supportive and entertainment purposes. If you're struggling, consider speaking with a mental health professional.")

suggestion_page()