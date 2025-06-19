import streamlit as st
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

def get_service_account_creds():
    """Builds credentials from the service account secret."""
    try:
        creds_json = dict(st.secrets.google_service_account)
        return service_account.Credentials.from_service_account_info(
            creds_json, scopes=['https://www.googleapis.com/auth/calendar']
        )
    except Exception as e:
        print(f"Service account credential error: {e}")
        return None

def get_oauth_creds():
    """Builds credentials from the user's stored OAuth token."""
    user_data = st.session_state.get('user_data')
    if not user_data or not user_data.get('refresh_token'):
        return None
    
    return Credentials(
        token=None,  # Access token is temporary, refresh token is key
        refresh_token=user_data.get('refresh_token'),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=st.secrets.google_oauth.client_id,
        client_secret=st.secrets.google_oauth.client_secret,
        scopes=['https://www.googleapis.com/auth/calendar']
    )

def create_calendar_for_password_user(username):
    """Uses the SERVICE ACCOUNT to create a new calendar."""
    creds = get_service_account_creds()
    if not creds: return None
    service = build('calendar', 'v3', credentials=creds)
    
    calendar_body = {
        'summary': f'Mental Health Plan - {username}',
        'timeZone': 'Etc/UTC'
    }
    try:
        created_calendar = service.calendars().insert(body=calendar_body).execute()
        calendar_id = created_calendar['id']
        
        # Share calendar with the user's email so they can see it in their Google account
        rule = {'role': 'writer', 'scope': {'type': 'user', 'value': st.session_state.user_data['email']}}
        # service.acl().insert(calendarId=calendar_id, body=rule).execute() # Optional: auto-share
        
        return calendar_id
    except Exception as e:
        print(f"Error creating calendar: {e}")
        return None

def add_events_to_calendar(events_to_add):
    """Adds a list of event dictionaries to the correct calendar based on user type."""
    user_data = st.session_state.user_data
    creds = None
    calendar_id = None

    if user_data.get('refresh_token'): # This is a Google user
        creds = get_oauth_creds()
        calendar_id = 'primary'
    elif user_data.get('google_calendar_id'): # This is a password user
        creds = get_service_account_creds()
        calendar_id = user_data.get('google_calendar_id')
    
    if not creds or not calendar_id:
        st.error("Could not determine user's calendar credentials.")
        return False

    service = build('calendar', 'v3', credentials=creds)
    success_count = 0
    for event in events_to_add:
        try:
            service.events().insert(calendarId=calendar_id, body=event).execute()
            success_count += 1
        except Exception as e:
            print(f"Error adding event '{event.get('summary')}': {e}")
    
    return success_count

def convert_ai_to_google_events(ai_events):
    """Converts the AI's schedule items into Google Calendar event format."""
    google_events = []
    today = datetime.now()
    day_map = {day: i for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])}

    for item in ai_events:
        day_str = item.get("day")
        if not day_str or day_str not in day_map: continue

        days_ahead = (day_map[day_str] - today.weekday() + 7) % 7
        event_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        google_events.append({
            'summary': item.get('activity'),
            'start': {'dateTime': f"{event_date}T{item.get('start_time')}", 'timeZone': 'Etc/UTC'},
            'end': {'dateTime': f"{event_date}T{item.get('end_time')}", 'timeZone': 'Etc/UTC'},
        })
    return google_events
