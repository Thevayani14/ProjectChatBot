# app.py

import streamlit as st
import os
import hashlib
from datetime import datetime
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import toml

# Local imports
from database import upsert_google_user, get_user_by_email, add_password_user, save_google_calendar_id
from google_calendar import create_calendar_for_password_user

# --- Initialize session state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_data" not in st.session_state:
    st.session_state.user_data = None

# --- MANUAL SECRETS LOADING & HELPERS (Copied from old login.py) ---
def load_secrets():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            return toml.load(f)
    except FileNotFoundError: return None
    except Exception as e: print(f"Error loading secrets.toml: {e}"); return None

SECRETS = load_secrets()
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis

1.  **Remove Manual Secret Loading:** We will trust that `st.secrets` is working and remove the `toml` loading. This simplifies the code. If it fails, the error message will be direct.
2.  **Remove the "Success Gate":** The `app.py` router is designed to handle showing the correct page. We will trust it to do its job and remove the complex logic from `login.py` that was trying to do the same thing.
3.  **One Single Goal for `login.py`:** The `login_page()` function's only job is to set `st.session_state.logged_in = True` and `st.session_state.user_data` upon a successful login, and then immediately `st.rerun()`. That's it. No other logic.

This strips the process down to its bare essentials.

---

### The Final, Simplest `login.py`

Please **replace the entire content of your `login.py` file** with this simplified version.

```python
import streamlit as st
import os
import hashlib
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Local imports
from database import upsert_google_user, get_user_by_email, add_password_user, save_google_calendar_id
from google_calendar import create_calendar_for_password_user

# --- CONSTANTS ---
SCOPES = [
    "openid",
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
    # This function is crucial for directing Google where to send the user back.
    if "STREAMLIT_SERVER_ADDRESS" in os.environ:
        return st.secrets.google_oauth.redirect_uri_prod
    else:
        return "http://localhost:8501"

# --- MAIN LOGIN PAGE ---
def login_page():
    # --- Part 1: Handle the redirect from Google if 'code' is in the URL ---
    query_params = st.query_params
    if 'code' in query_params and 'auth_code_processed' not in st.session_state:
        st.session_state.auth_code_processed = True
        code = query_params.get("code")
        try:
            with st.spinner("Finalizing authentication..."):
                client_config = {
                    "web": {
                        "client_id": st.secrets.google_oauth.client_id,
                        "client_secret": st.secrets.google_oauth.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": [get_redirect_uri()]
                    }
                }
                flow = Flow.from_client_config(
                    client_config=client_config, scopes=SCOPES, redirect_uri=get_redirect_uri()
                )
                flow.fetch_token(code=code)
                creds = flow.credentials
                
                user.com/auth/calendar"]

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

def get_redirect_uri():
    if "STREAMLIT_SERVER_ADDRESS" in os.environ:
        return st.secrets.google_oauth.redirect_uri_prod
    else:
        return "http://localhost:8501"

def get_client_config():
    oauth_secrets = None
    if SECRETS and "google_oauth" in SECRETS: oauth_secrets = SECRETS["google_oauth"]
    elif hasattr(st.secrets, "google_oauth"): oauth_secrets = st.secrets.google_oauth
    if not oauth_secrets: return None
    return {"web": {"client_id": oauth_secrets["client_id"], "client_secret": oauth_secrets["client_secret"], "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "redirect_uris": [get_redirect_uri()]}}

# --- MAIN APP LOGIC (THE GATEKEEPER) ---
st.set_page_config(page_title="Login", layout="centered")

# If user is already logged in, show welcome and hide login UI
if st.session_state.logged_in:
    display_name = st.session_state.user_data.get('full_name') or st.session_state.user_data.get('username')
    st.title(f"Welcome, {display_name}!")
    st.markdown("You are logged in. Please select a page from the sidebar to continue.")
    st.sidebar.success("Signed in successfully!")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_data = None
        st.rerun()
else:
    # --- Show the Login UI if not logged in ---
    st.title("Welcome! Sign In or Create an Account")
    st.write("Choose your preferred method to get started.")

    query_params = st.query_params
    code = query_params.get("code")

    if code and "auth_code_processed" not in st.session_state:
        st.session_state.auth_code_processed = True
        try:
            with st.spinner("Finalizing authentication..."):
                client_config = get_client_config()
                flow = Flow.from_client_config(client_config=client_config, scopes=SCOPES, redirect_uri=get_redirect_uri())
                flow.fetch_token(code=code)
                creds = flow.credentials
                user_info_service = build('oauth2', 'v2', credentials=creds)
                user_info = user_info_service.userinfo().get().execute()
                email = user_info.get('email')
                full_name = user_info.get('name')
                
                upsert_google_user(email=email, full_name=full_name, refresh_token=creds.refresh_token)
                
                st.session_state.logged_in = True
                st.session_state.user_data = get_user_by_email(email)
                
                st.query_params.clear()
                st.rerun()
        except Exception as e:
            st.error(f"An error occurred during authentication: {e}")
            del st.session_state.auth_code_processed

    else:
        google_tab, password_tab = st.tabs(["✨ Sign in with Google", "🔑 Use Email & Password"])
        with google_tab:
            client_config = get_client_config()
            if not client_config:
                st.error("OAuth credentials are not configured correctly.")
            else:
                flow_for_link = Flow.from_client_config(client_config=client_config, scopes=SCOPES, redirect_uri=get_redirect_uri())
                authorization_url, _ = flow_for_link.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
                st.link_button("Sign in with Google", authorization_url, use_container_width=True, type="primary")
        
        with password_tab:
            login_form, signup_form = st.tabs(["Login", "Sign Up"])
            with login_form:
                with st.form("password_login_form"):
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    submitted = st.form_submit_button("Login")
                    if submitted:
                        user_data = get_user_by_email(email)
                        if user_data and user_data.get('hashed_password') and verify_password(user_data['hashed_password'], password):
                            st.session_state.logged_in = True
                            st.session_state.user_data = user_data
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")
            
            with signup_form:
                with st.form("password_signup_form"):
                    email = st.text_input("Email*", key="signup_email")
                    username = st.text_input("Username*", key="signup_username")
                    new_password = st.text_input("Password*", type="password", key="signup_pass")
                    confirm_password = st.text_input("Confirm Password*", type="password", key="signup_conf_pass")
                    submitted = st.form_submit_button("Create Account")
                    if submitted:
                        if not (email and username and new_password): st.error("Please fill all required fields.")
                        elif new_password != confirm_password: st.error("Passwords do not match.")
                        elif get_user_by_email(email): st.error("An account with this email already exists.")
                        else:
                            with st.spinner("Setting up your account..."):
                                calendar_id = create_calendar_for_password_user(username, email)
                                if calendar_id:
                                    hashed_pass = hash_password(new_password)
                                    if add_password_user(email, username, hashed_pass, calendar_id):
                                        st.success("Account created! Please go to the Login tab.")
                                    else: st.error("Failed to save user.")
                                else: st.error("Could not create supporting calendar.")
