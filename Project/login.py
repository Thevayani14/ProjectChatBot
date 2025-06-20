import streamlit as st
import os
import hashlib
from datetime import datetime
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import toml # Import the toml library

# Local imports
from database import upsert_google_user, get_user_by_email, add_password_user
from google_calendar import create_calendar_for_password_user

# --- MANUAL SECRETS LOADING FUNCTION ---
def load_secrets():
    """Manually loads the secrets.toml file for robust local execution."""
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            return toml.load(f)
    except FileNotFoundError:
        # This will happen on Streamlit Cloud, which is fine because st.secrets will be used there.
        print("Local secrets.toml not found, assuming execution on Streamlit Cloud.")
        return None
    except Exception as e:
        print(f"Error loading secrets.toml: {e}")
        return None

# Load secrets once at the start.
SECRETS = load_secrets()

# --- CONSTANTS ---
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
    # On Streamlit Cloud, it MUST use the one from secrets.
    if "STREAMLIT_SERVER_ADDRESS" in os.environ:
        return st.secrets.google_oauth.redirect_uri_prod
    else:
        # For local development
        return "http://localhost:8501"

# --- MAIN LOGIN PAGE ---
def login_page():
    st.title("Welcome! Sign In or Create an Account")
    st.write("Choose your preferred method to get started.")

    google_tab, password_tab = st.tabs(["✨ Sign in with Google", "🔑 Use Email & Password"])

    with google_tab:
        st.info("The easiest and most secure way to get started and sync with your calendar.")
        
        # --- ROBUST CREDENTIALS ACCESS ---
        # Try to get OAuth secrets first from the manually loaded file, then from st.secrets as a fallback.
        oauth_secrets = None
        if SECRETS and "google_oauth" in SECRETS:
            oauth_secrets = SECRETS["google_oauth"]
        elif hasattr(st.secrets, "google_oauth"):
             oauth_secrets = st.secrets.google_oauth
        
        if not oauth_secrets:
            st.error("OAuth credentials are not configured correctly. Please check your secrets.toml file.")
            return

        client_config = {
            "web": {
                "client_id": oauth_secrets["client_id"],
                "client_secret": oauth_secrets["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [get_redirect_uri()]
            }
        }
        
        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=SCOPES,
            redirect_uri=get_redirect_uri()
        )
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        st.link_button("Sign in with Google", authorization_url, use_container_width=True, type="primary")

        query_params = st.query_params
        code = query_params.get("code")

        if code and "auth_code" not in st.session_state:
            try:
                with st.spinner("Authenticating with Google..."):
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    
                    user_info_service = build('oauth2', 'v2', credentials=creds)
                    user_info = user_info_service.userinfo().get().execute()

                    email = user_info.get('email')
                    full_name = user_info.get('name')
                    
                    user_id = upsert_google_user(
                        email=email, 
                        full_name=full_name, 
                        refresh_token=creds.refresh_token
                    )
                    
                    st.session_state.logged_in = True
                    st.session_state.user_data = get_user_by_email(email)
                    st.session_state.auth_code = code
                    st.session_state.page = 'homepage'
                    st.rerun()
            except Exception as e:
                st.error(f"An error occurred during authentication: {e}")

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
                            calendar_id = create_calendar_for_password_user(username, email)
                            if calendar_id:
                                hashed_pass = hash_password(new_password)
                                if add_password_user(email, username, hashed_pass, calendar_id):
                                    # After creating user, also save the calendar_id to the new user record in DB
                                    new_user_data = get_user_by_email(email)
                                    from database import save_google_calendar_id # local import to avoid circular dependency
                                    save_google_calendar_id(new_user_data['id'], calendar_id)
                                    st.success("Account created successfully! Please proceed to the Login tab.")
                                else:
                                    st.error("Failed to save user to database.")
                            else:
                                st.error("Could not create a supporting calendar. Please try again later.")
