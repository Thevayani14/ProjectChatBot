import streamlit as st
import hashlib
from database import get_user_by_email, add_password_user, update_user_password
from styles import get_dark_mode_css  # Your custom dark theme

# --- Page Config & Global Styling ---
st.set_page_config(page_title="Login - Mental Health Companion", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
st.markdown(get_dark_mode_css(), unsafe_allow_html=True)

# --- Hero Banner with Custom Title ---
st.markdown("""
<style>
.hero-banner {
    background: linear-gradient(90deg, #141e30 0%, #243b55 100%);
    padding: 2.5rem 1rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.6);
}
.hero-banner h1 {
    color: #e0e0e0;
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: 1px;
    text-shadow: 1px 1px 6px rgba(0,0,0,0.4);
    margin: 0;
}
</style>
<div class="hero-banner">
    <h1>🌱 Mental Health Companion</h1>
</div>
""", unsafe_allow_html=True)



# --- Helper Functions ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "reset_email" not in st.session_state:
    st.session_state.reset_email = ""

# --- Redirect if Already Logged In ---
if st.session_state.logged_in:
    st.switch_page("pages/1_🏠_Homepage.py")

# --- LOGIN PAGE ---
if st.session_state.page == "login":
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    st.caption("Log in, sign up, or reset your password.")

    login_tab, signup_tab = st.tabs(["🔑 Login", "✍️ Sign Up"])

    # --- 🔑 Login ---
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_submit = st.form_submit_button("🔓 Login")

            if login_submit:
                user_data = get_user_by_email(email)
                if user_data and verify_password(user_data['hashed_password'], password):
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_data
                    st.success(f"✅ Welcome back, {user_data['username']}!")
                    st.session_state.page = "homepage"
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password.")

        st.markdown("---")
        if st.button("🔐 Forgot Password?"):
            st.session_state.page = "reset_password"
            st.rerun()

    # --- ✍️ Sign Up ---
    with signup_tab:
        with st.form("signup_form"):
            email = st.text_input("Email*", key="signup_email", placeholder="e.g. you@example.com")
            username = st.text_input("Username*", key="signup_username", placeholder="Choose a username")
            new_password = st.text_input("Password*", type="password", key="signup_pass1", placeholder="Enter password")
            confirm_password = st.text_input("Confirm Password*", type="password", key="signup_pass2", placeholder="Re-enter password")
            signup_submit = st.form_submit_button("Create Account")

            if signup_submit:
                if not (email and username and new_password and confirm_password):
                    st.error("⚠️ Please fill in all required fields.")
                elif new_password != confirm_password:
                    st.error("⚠️ Passwords do not match.")
                elif get_user_by_email(email):
                    st.error("❌ An account with this email already exists.")
                else:
                    hashed_pass = hash_password(new_password)
                    success = add_password_user(email, username, hashed_pass)
                    if success:
                        st.success("✅ Account created successfully! You can now log in.")
                    else:
                        st.error("❌ Failed to create account. Try again.")

    st.markdown('</div>', unsafe_allow_html=True)

# --- 🔐 Reset Password ---
elif st.session_state.page == "reset_password":
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.title("🔐 Reset Password")
    st.caption("Enter your email and a new password.")

    with st.form("reset_form"):
        reset_email = st.text_input("Registered Email", value=st.session_state.reset_email, placeholder="Enter your email")
        new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
        confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Re-enter new password")
        reset_submit = st.form_submit_button("Reset Password")

        if reset_submit:
            user = get_user_by_email(reset_email)
            if not user:
                st.error("❌ Email not found.")
            elif not new_password:
                st.error("⚠️ Please enter a new password.")
            elif new_password != confirm_password:
                st.error("⚠️ Passwords do not match.")
            else:
                hashed_new = hash_password(new_password)
                update_user_password(reset_email, hashed_new)
                st.success("✅ Password reset successful.")
                st.session_state.page = "login"
                st.session_state.reset_email = ""
                st.rerun()

    st.markdown("---")
    if st.button("⬅️ Back to Login"):
        st.session_state.page = "login"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
