import streamlit as st
import os
import hashlib
from datetime import datetime
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from database import upsert_google_user, get_user_by_email, add_password_user
from google_calendar import create_calendar_for_password_user

# --- CONSTANTS ---
CLIENT_SECRETS_DICT = {
    "web": {
        "client_id": st.secrets.google_oauth.client_id,
        "client_secret": st.secrets.google_oauth.client_secret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": [
            "http://localhost:8501", # For local
            st.secrets.google_oauth.redirect_uri_prod # For deployed
        ]
    }
}
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/calendar"
]

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
        return "http://localhost:8501"

# --- MAIN LOGIN PAGE ---
def login_page():
    st.title("Welcome! Sign In or Create an Account")
    st.write("Choose your preferred method to get started.")

    google_tab, password_tab = st.tabs(["✨ Sign in with Google", "🔑 Use Email & Password"])

    # --- GOOGLE OAUTH TAB ---
    with google_tab:
        st.write("The easiest and most secure way to get started.")
        
        # Create the OAuth flow object
        flow = Flow.from_client_config(
            client_config=CLIENT_SECRETS_DICT,
            scopes=SCOPES,
            redirect_uri=get_redirect_uri()
        )
        
        # Generate the authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Display the login button as a link
        st.link_button("Sign in with Google", authorization_url, use_container_width=True, type="primary")

        # Check for the authorization code in the URL query parameters
        query_params = st.query_params
        code = query_params.get("code")

        if code and "code" not in st.session_state:
            try:
                # Exchange the code for tokens
                flow.fetch_token(code=code)
                creds = flow.credentials
                
                # Use the credentials to get user info
                user_info_service = build('oauth2', 'v2', credentials=creds)
                user_info = user_info_service.userinfo().get().execute()

                email = user_info.get('email')
                full_name = user_info.get('name')
                
                # Save or update user in our database
                user_id = upsert_google_user(
                    email=email, 
                    full_name=full_name, 
                    refresh_token=creds.refresh_token
                )
                
                # Log the user in
                st.session_state.logged_in = True
                st.session_state.user_data = get_user_by_email(email)
                st.session_state.code = code # Prevent re-running this block
                st.session_state.page = 'homepage'
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred during authentication: {e}")

    # --- EMAIL/PASSWORD TAB ---
    with password_tab:
        # This part of the code remains exactly the same as before
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
                            calendar_id = create_calendar_for_password_user(username, email) # Pass email to share
                            if calendar_id:
                                hashed_pass = hash_password(new_password)
                                add_password_user(email, username, hashed_pass, calendar_id)
                                st.success("Account created successfully! Please proceed to the Login tab.")
                            else:
                                st.error("Could not create supporting calendar. Please try again later.")
