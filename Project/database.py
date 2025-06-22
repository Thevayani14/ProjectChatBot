import streamlit as st
import psycopg2
import psycopg2.extras
from contextlib import closing

def connect_db():
    try:
        conn = psycopg2.connect(**st.secrets.database)
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Database connection failed: {e}")
        return None

def add_password_user(email, username, hashed_password):
    sql = "INSERT INTO users (email, username, full_name, hashed_password) VALUES (%s, %s, %s, %s)"
    try:
        with closing(connect_db()) as db, closing(db.cursor()) as cursor:
            cursor.execute(sql, (email, username, username, hashed_password))
        db.commit()
        return True
    except Exception as e:
        print(f"Error creating password user: {e}")
        return False

# ... (Paste all the conversation and score functions here. They are unchanged.)
# get_user_by_email, create_conversation, get_user_conversations, add_message,
# get_messages, delete_conversation, update_conversation_score, get_latest_assessment_score

# --- CALENDAR EVENT FUNCTIONS ---
def save_calendar_events(user_id, events, is_generated=True):
    if is_generated:
        delete_sql = "DELETE FROM calendar_events WHERE user_id = %s AND is_generated = TRUE"
        with closing(connect_db()) as db, closing(db.cursor()) as cursor:
            cursor.execute(delete_sql, (user_id,))
        db.commit()

    insert_sql = "INSERT INTO calendar_events (user_id, event_date, title, start_time, end_time, color, is_generated) VALUES %s"
    event_tuples = []
    for e in events:
        event_date = e['start'].split('T')[0]
        start_time = e['start'].split('T')[1] if 'T' in e['start'] else None
        end_time = e['end'].split('T')[1] if 'T' in e['end'] else None
        event_tuples.append((user_id, event_date, e['title'], start_time, end_time, e.get('color', '#6f42c1'), is_generated))
    
    if not event_tuples: return True
    try:
        with closing(connect_db()) as db, closing(db.cursor()) as cursor:
            psycopg2.extras.execute_values(cursor, insert_sql, event_tuples)
        db.commit()
        return True
    except Exception as e:
        print(f"Error saving calendar events: {e}")
        return False

def get_calendar_events(user_id):
    sql = "SELECT id, event_date, title, start_time, end_time, color FROM calendar_events WHERE user_id = %s"
    with closing(connect_db()) as db, closing(db.cursor()) as cursor:
        cursor.execute(sql, (user_id,))
        events = [{"id": str(r[0]), "start": f"{r[1]}T{r[2]}" if r[2] else str(r[1]), "end": f"{r[1]}T{r[3]}" if r[3] else str(r[1]), "title": r[4], "color": r[5]} for r in cursor.fetchall()]
        return events

def delete_calendar_event(event_id):
    sql = "DELETE FROM calendar_events WHERE id = %s"
    with closing(connect_db()) as db, closing(db.cursor()) as cursor:
        cursor.execute(sql, (event_id,))
    db.commit()
    return True
