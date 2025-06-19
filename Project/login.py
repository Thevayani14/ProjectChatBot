import streamlit as st
from st_oauth import st_oauth
import os
import hashlib
from datetime import datetime

from database import upsert_google_user, get_user_by_email, add_password_user
from google_calendar import create_calendar_for_password_user

# --- PASSWORD HASHING ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

# --- HELPER FOR OAUTH REDIRECT URI ---
def get_redirect_uri():
    if "STREAMLIT_SERVER_ADDRESS" in os.environ:
        return st.secrets.google_oauth.redirect_uri_prod
    else:
        # For local development
        return "http://localhost:8501"

def login_page():
    """Displays a hybrid login page with Google OAuth and Email/Password options."""
    st.title("Welcome! Sign In or Create an Account")
    st.write("Choose your preferred method to get started.")

    google_tab, password_tab = st.tabs(["✨ Sign in with Google", "🔑 Use Email & Password"])

    # --- GOOGLE OAUTH TAB ---
    with google_tab:
        st.write("The easiest and most secure way to get started.")
        client_id = st.secrets.google_oauth.client_id
        client_secret = st.secrets.google_oauth.client_secret
        redirect_uri = get_redirect_uri()
        scopes = [
            "https.www.googleapis.com/auth/userinfo.profile",
            "https.www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/calendar"
        ]

        # The st_oauth component handles the button and redirects
        token = st_oauth(
            client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri,
            scopes=scopes, authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
            refresh_endpoint="https://oauth2.googleapis.com/token",
            button_text="Sign in with Google", button_type="primary"
        )

        if token:
            user_info = token['userinfo']
            email = user_info.get('email')
            full_name = user_info.get('name')
            
            # Save or update user in our database
            user_id = upsert_google_user(email, full_name, token.get('refresh_token'))
            
            # Log the user in
            st.session_state.logged_in = True
            st.session_state.user_data = get_user_by_email(email) # Fetch the complete user record
            st.session_state.page = 'homepage'
            st.rerun()

    # --- EMAIL/PASSWORD TAB ---
    with password_tab:
        login_form_tab, signup_form_tab = st.tabs(["Login", "Sign Up"])
        
        with login_form_tab:
            with st.form("password_login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")

                if submitted:
                    user_data = get_user_by_email(email)
                    if user_data and user_data.get('hashed_password') and verify_password(user_data['hashed_password'], password):
                        st.session_state.logged_in = True
                        st.session_state.user_data = user_data
                        st.session_state.page = 'homepage'
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
        
        with signup_form_tab:
            with st.form("password_signup_form"):
                email = st.text_input("Email*")
                username = st.text_input("Username*")
                new_password = st.text_input("Password*", type="password")
                confirm_password = st.text_input("Confirm Password*", type="password")
                submitted = st.form_submit_button("Create Account")

                if submitted:
                    if not (email and username and new_password):
                        st.error("Please fill in all required fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif get_user_by_email(email):
                        st.error("An account with this email already exists.")
                    else:
                        with st.spinner("Setting up your account and personal calendar..."):
                            calendar_id = create_calendar_for_password_user(username)
                            if calendar_id:
                                hashed_pass = hash_password(new_password)
                                add_password_user(email, username, hashed_pass, calendar_id)
                                st.success("Account created successfully! Please proceed to the Login tab.")
                            else:
                                st.error("Could not create supporting calendar. Please try again later.")
