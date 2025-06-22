import streamlit as st
import hashlib
from database import get_user_by_email, add_password_user
from sidebar import sidebar

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Password Hashing
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

# Main App Logic
st.set_page_config(page_title="Mental Health Companion", layout="centered")

if st.session_state.get("logged_in"):
    sidebar()
    display_name = st.session_state.user_data.get('full_name') or st.session_state.user_data.get('username')
    st.title(f"Welcome, {display_name}!")
    st.success("You are logged in. Please select a page from the sidebar.")
else:
    st.title("Welcome! Sign In or Create an Account")
    login_tab, signup_tab = st.tabs(["🔑 Login", "✍️ Sign Up"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                user_data = get_user_by_email(email)
                if user_data and verify_password(user_data['hashed_password'], password):
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_data
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
    
    with signup_tab:
        with st.form("signup_form"):
            email = st.text_input("Email*")
            username = st.text_input("Username*")
            new_password = st.text_input("Password*", type="password")
            confirm_password = st.text_input("Confirm Password*", type="password")
            if st.form_submit_button("Create Account"):
                if not (email and username and new_password):
                    st.error("Please fill all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif get_user_by_email(email):
                    st.error("Email already registered.")
                else:
                    hashed_pass = hash_password(new_password)
                    if add_password_user(email, username, hashed_pass):
                        st.success("Account created! Please proceed to the Login tab.")
                    else:
                        st.error("Failed to create account.")
