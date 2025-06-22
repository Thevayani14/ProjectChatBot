import streamlit as st
import hashlib
from database import get_user_by_email, add_password_user
from google_calendar import create_calendar_for_password_user
from sidebar import sidebar

# --- Initialize session state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- PASSWORD HASHING ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_password(stored_hash, provided_password):
    return stored_hash == hash_password(provided_password)

# --- THE APP's MAIN FUNCTION ---
def main():
    st.set_page_config(page_title="Mental Health Companion", layout="centered")

    # --- Gatekeeper Logic ---
    if st.session_state.get("logged_in"):
        # If logged in, show the sidebar and a welcome message.
        sidebar()
        display_name = st.session_state.user_data.get('full_name') or st.session_state.user_data.get('username')
        st.title(f"Welcome, {display_name}!")
        st.success("You are logged in.")
        st.markdown("Please select a page from the sidebar to get started.")
    else:
        # --- If not logged in, show the login/signup UI ---
        st.title("Welcome! Sign In or Create an Account")
        
        login_tab, signup_tab = st.tabs(["🔑 Login", "✍️ Sign Up"])

        with login_tab:
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
        
        with signup_tab:
            with st.form("password_signup_form"):
                email = st.text_input("Email*", key="signup_email")
                username = st.text_input("Username*", key="signup_username")
                new_password = st.text_input("Password*", type="password", key="signup_pass")
                confirm_password = st.text_input("Confirm Password*", type="password", key="signup_conf_pass")
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
                                    st.success("Account created successfully! Please proceed to the Login tab.")
                                else:
                                    st.error("Failed to save user to database.")
                            else:
                                st.error("Could not create supporting calendar. Please try again later.")

if __name__ == "__main__":
    main()
