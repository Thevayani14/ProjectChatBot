import streamlit as st
import psycopg2
import psycopg2.extras
from contextlib import closing
import pandas as pd
from datetime import datetime, timedelta
import textwrap
# --- DATABASE CONNECTION ---
def connect_db():
    """Connects to the PostgreSQL database using credentials from st.secrets."""
    try:
        conn = psycopg2.connect(
            host=st.secrets.database.host,
            port=st.secrets.database.port,
            dbname=st.secrets.database.dbname,
            user=st.secrets.database.user,
            password=st.secrets.database.password
        )
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Database connection failed: {e}")
        return None

# --- USER MANAGEMENT FUNCTIONS ---
def add_password_user(email, username, hashed_password):
    sql = "INSERT INTO users (email, username, full_name, hashed_password) VALUES (%s, %s, %s, %s)"
    conn = None
    try:
        conn = connect_db()
        if not conn: return False
        with conn.cursor() as cursor:
            cursor.execute(sql, (email, username, username, hashed_password))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating password user: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

# --- READ-ONLY FUNCTIONS (can use the simpler 'with closing') ---
def get_user_by_email(email):
    sql = "SELECT id, email, username, full_name, hashed_password FROM users WHERE email = %s"
    try:
        with closing(connect_db()) as db, closing(db.cursor()) as cursor:
            if db is None: return None
            cursor.execute(sql, (email,))
            user_data = cursor.fetchone()
            if user_data:
                columns = ['id', 'email', 'username', 'full_name', 'hashed_password']
                return dict(zip(columns, user_data))
            return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None

def update_user_password(email, new_hashed_password):
    sql = "UPDATE users SET hashed_password = %s WHERE email = %s"
    try:
        with closing(connect_db()) as db, closing(db.cursor()) as cursor:
            cursor.execute(sql, (new_hashed_password, email))
            db.commit()
            return True
    except Exception as e:
        print(f"[DB Error] Failed to update password for {email}: {e}")
        return False


# --- CONVERSATION & MESSAGE FUNCTIONS ---
def create_conversation(user_id, title="New Chat"):
    sql = "INSERT INTO conversations (user_id, title) VALUES (%s, %s) RETURNING id"
    with closing(connect_db()) as db:
        if db is None: return None
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id, title))
            new_id = cursor.fetchone()[0]
        db.commit()
        return new_id

# def get_user_conversations(user_id):
#     sql = "SELECT id, title FROM conversations WHERE user_id = %s ORDER BY start_time DESC"
#     with closing(connect_db()) as db:
#         if db is None: return []
#         with closing(db.cursor()) as cursor:
#             cursor.execute(sql, (user_id,))
#             conversations = [{"id": row[0], "title": row[1]} for row in cursor.fetchall()]
#             return conversations

def get_user_conversations(user_id):
    """Fetches all conversations for a user, including score and video_url."""
    sql = "SELECT id, title, completion_score, video_url FROM conversations WHERE user_id = %s ORDER BY start_time DESC"
    with closing(connect_db()) as db:
        if db is None: return []
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            # Updated to handle the new 'video_url' column
            conversations = [
                {"id": row[0], "title": row[1], "completion_score": row[2], "video_url": row[3]} 
                for row in cursor.fetchall()
            ]
            return conversations

# ADD this new function to your database.py file
def update_conversation_video_url(conversation_id, video_url):
    """Updates the video_url for a completed assessment conversation."""
    sql = "UPDATE conversations SET video_url = %s WHERE id = %s"
    with closing(connect_db()) as db:
        if db is None: return
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (video_url, conversation_id))
        db.commit()

def delete_conversation(conversation_id):
    """Deletes a conversation and its associated messages from the database."""
    # The ON DELETE CASCADE constraint will automatically delete chat_history messages.
    sql = "DELETE FROM conversations WHERE id = %s"
    with closing(connect_db()) as db:
        if db is None: return False
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (conversation_id,))
        db.commit()
        return True

        
# def update_conversation_title(conversation_id, title):
#     sql = "UPDATE conversations SET title = %s WHERE id = %s"
#     with closing(connect_db()) as db:
#         if db is None: return
#         with closing(db.cursor()) as cursor:
#             cursor.execute(sql, (title, conversation_id))
#         db.commit()

def add_message(conversation_id, role, content):
    sql = "INSERT INTO chat_history (conversation_id, role, content) VALUES (%s, %s, %s)"
    with closing(connect_db()) as db:
        if db is None: return
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (conversation_id, role, content))
        db.commit()

def get_messages(conversation_id):
    sql = "SELECT role, content FROM chat_history WHERE conversation_id = %s ORDER BY timestamp ASC"
    with closing(connect_db()) as db:
        if db is None: return []
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (conversation_id,))
            messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
            return messages
        
def log_behavior(user_id, date, hours, solo_ratio, late_night, mood, social_score, breaks, risk_score):
    sql = """
    INSERT INTO behavior_logs (
        user_id, log_date, hours_played, solo_play_ratio,
        late_night_gaming, mood_score, social_interaction_score,
        physical_breaks, risk_score
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with closing(connect_db()) as db:
        if db is None: return
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (
                user_id, date, hours, solo_ratio, late_night,
                mood, social_score, breaks, risk_score
            ))
        db.commit()

def get_todays_events(user_id, today_date):
    """Fetches all calendar events for a user for a specific date."""
    sql = """
        SELECT title, start_time
        FROM calendar_events
        WHERE user_id = %s AND event_date = %s
        ORDER BY start_time ASC;
    """
    try:
        with closing(connect_db()) as db:
            if db is None: return []
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (user_id, today_date))
                # Fetchall will return a list of tuples, e.g., [('Do this', datetime.time(9, 0))]
                return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching today's events for user {user_id}: {e}")
        return []

def update_conversation_score(conversation_id, score):
    sql = "UPDATE conversations SET completion_score = %s WHERE id = %s"
    conn = None
    try:
        conn = connect_db()
        if not conn: return False
        with conn.cursor() as cursor:
            cursor.execute(sql, (score, conversation_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating score: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()


def save_calendar_events(user_id, events_to_save, is_generated):
    conn = None
    try:
        conn = connect_db()
        if not conn: return False
        with conn.cursor() as cursor:
            if is_generated:
                cursor.execute("DELETE FROM calendar_events WHERE user_id = %s AND is_generated = TRUE", (user_id,))
            sql_insert = """
                INSERT INTO calendar_events (user_id, title, start_time, end_time, color, is_generated)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            data_to_insert = [
                (user_id, event['title'], event['start'], event['end'], event.get('color', '#6f42c1'), is_generated) 
                for event in events_to_save
            ]
            psycopg2.extras.execute_batch(cursor, sql_insert, data_to_insert)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"DB error in save_calendar_events: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

def get_calendar_events(user_id):
    """Fetches all calendar events, now including completion and mood status."""
    sql = "SELECT id, title, start_time, end_time, color, is_generated, completed, user_mood FROM calendar_events WHERE user_id = %s"
    events = []
    with closing(connect_db()) as db:
        if db is None: return []
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            for row in cursor.fetchall():
                events.append({
                    "id": str(row[0]), "title": row[1], "start": row[2].isoformat(),
                    "end": row[3].isoformat(), "color": row[4], "is_generated": row[5],
                    "completed": row[6], "user_mood": row[7]
                })
    return events

def update_calendar_event_completion(event_id, completed, user_mood):
    """Updates the completion status and mood for a specific event."""
    sql = "UPDATE calendar_events SET completed = %s, user_mood = %s WHERE id = %s"
    with closing(connect_db()) as db:
        if db is None: return False
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (completed, user_mood, event_id))
        db.commit()
        return True

def get_events_for_last_week(user_id):
    """Fetches completed and skipped events from the past 7 days for the weekly review."""
    seven_days_ago = datetime.now() - timedelta(days=7)
    sql = "SELECT title, completed, user_mood FROM calendar_events WHERE user_id = %s AND start_time >= %s"
    with closing(connect_db()) as db:
        if db is None: return []
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id, seven_days_ago))
            return cursor.fetchall()

def delete_calendar_event(event_id):
    sql = "DELETE FROM calendar_events WHERE id = %s"
    conn = None
    try:
        conn = connect_db()
        if not conn: return False
        with conn.cursor() as cursor:
            cursor.execute(sql, (event_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting event: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

# In database.py, REPLACE the old function with this one.

def update_calendar_event(event_id, new_date, new_start_time, new_end_time):
    """Updates the start and end times of an existing event."""
    final_start_time = new_start_time if new_start_time is not None else time(0, 0)
    new_start_timestamp = f"{new_date}T{final_start_time}"
    if new_end_time is None:
        end_dt = datetime.combine(new_date, final_start_time) + timedelta(hours=1)
        new_end_timestamp = end_dt.isoformat()
    else:
        new_end_timestamp = f"{new_date}T{new_end_time}"
    sql = """
        UPDATE calendar_events
        SET start_time = %s, end_time = %s
        WHERE id = %s
    """
    conn = None
    try:
        conn = connect_db()
        if not conn: return False
        with conn.cursor() as cursor:
            cursor.execute(sql, (new_start_timestamp, new_end_timestamp, event_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating event {event_id}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

def clear_all_events(user_id):
    """Deletes all calendar events for a specific user."""
    sql = "DELETE FROM calendar_events WHERE user_id = %s"
    conn = None
    try:
        conn = connect_db()
        if not conn: return False
        with conn.cursor() as cursor:
            cursor.execute(sql, (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error clearing all events for user {user_id}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

# def get_latest_assessment_score(user_id):
#     sql = "SELECT completion_score FROM conversations WHERE user_id = %s AND completion_score IS NOT NULL ORDER BY start_time DESC LIMIT 1"
#     with closing(connect_db()) as db, closing(db.cursor()) as cursor:
#         if db is None: return None
#         cursor.execute(sql, (user_id,))
#         result = cursor.fetchone()
#         return result[0] if result else None



        
def update_conversation_answers(conversation_id, answers):
    sql = "UPDATE conversations SET answers = %s WHERE id = %s"
    with closing(connect_db()) as db:
        if db is None: return
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (answers, conversation_id))
        db.commit()

def get_latest_assessment_answers(user_id):
    sql = "SELECT answers FROM conversations WHERE user_id = %s AND answers IS NOT NULL ORDER BY start_time DESC LIMIT 1;"
    with closing(connect_db()) as db:
        if db is None: return None
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        
# Add this new function to your database.py file

def get_score_trend(user_id):
    """Fetches the last two completed assessment scores to determine a trend."""
    sql = """
        SELECT completion_score 
        FROM conversations 
        WHERE user_id = %s 
          AND completion_score IS NOT NULL 
          AND title LIKE 'PHQ-9 Assessment%%'
        ORDER BY start_time DESC
        LIMIT 2;
    """
    with closing(connect_db()) as db:
        if db is None: return (None, None)
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            scores = [row[0] for row in cursor.fetchall()]
            if len(scores) == 2:
                # Returns (latest_score, previous_score)
                return (scores[0], scores[1])
            elif len(scores) == 1:
                # Returns (latest_score, None) if only one score exists
                return (scores[0], None)
            else:
                return (None, None)
            
# In database.py, REPLACE the old function with this one.

def get_todays_events(user_id, today_date):
    """
    Fetches all calendar events for a user for a specific date by checking
    if the start_time falls within that day.
    """
    # The start of today is the date itself (e.g., '2025-07-16 00:00:00')
    start_of_day = today_date
    # The end of today is 24 hours after the start
    end_of_day = today_date + timedelta(days=1)

    # This query correctly uses the start_time column.
    sql = """
        SELECT title, start_time
        FROM calendar_events
        WHERE user_id = %s 
          AND start_time >= %s 
          AND start_time < %s
        ORDER BY start_time ASC;
    """
    try:
        with closing(connect_db()) as db:
            if db is None: return []
            with closing(db.cursor()) as cursor:
                # We pass the start_of_day and end_of_day as parameters
                cursor.execute(sql, (user_id, start_of_day, end_of_day))
                # The result is a list of tuples, e.g., [('Yoga', datetime.time(9, 0))]
                # We need to extract just the time part for display.
                events = []
                for title, start_timestamp in cursor.fetchall():
                    # The database returns a full datetime object, we extract the time.
                    events.append((title, start_timestamp.time()))
                return events
    except Exception as e:
        print(f"Error fetching today's events for user {user_id}: {e}")
        return []
    
def clear_all_assessments(user_id):
    """
    Finds all conversations that are PHQ-9 assessments for a user and deletes them.
    """
    try:
        # Get all conversations for the user
        all_conversations = get_user_conversations(user_id)
        
        # Filter to find only the assessment conversations
        assessment_ids_to_delete = [
            conv['id'] for conv in all_conversations 
            if conv.get('title', '').startswith("PHQ-9 Assessment")
        ]
        
        if not assessment_ids_to_delete:
            print(f"No assessments to clear for user_id {user_id}")
            return True # Nothing to do, so it's a success

        # Loop through and delete each assessment
        # This reuses the existing delete_conversation logic, which is good practice
        for conv_id in assessment_ids_to_delete:
            delete_conversation(conv_id)
            
        print(f"Successfully cleared {len(assessment_ids_to_delete)} assessments for user_id {user_id}")
        return True

    except Exception as e:
        print(f"An error occurred while clearing all assessments for user {user_id}: {e}")
        return False



import streamlit as st
import psycopg2
import psycopg2.extras
from contextlib import closing
import pandas as pd
from datetime import datetime, timedelta, date, time

# --- DATABASE CONNECTION ---
def connect_db():
    """Connects to the PostgreSQL database using credentials from st.secrets."""
    try:
        conn = psycopg2.connect(
            host=st.secrets.database.host,
            port=st.secrets.database.port,
            dbname=st.secrets.database.dbname,
            user=st.secrets.database.user,
            password=st.secrets.database.password
        )
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Database connection failed: {e}")
        return None

# --- USER MANAGEMENT ---
def add_password_user(email, username, hashed_password):
    sql = "INSERT INTO users (email, username, full_name, hashed_password) VALUES (%s, %s, %s, %s)"
    with closing(connect_db()) as db:
        if db is None: return False
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (email, username, username, hashed_password))
            db.commit()
    return True

def get_user_by_email(email):
    sql = "SELECT id, email, username, full_name, hashed_password FROM users WHERE email = %s"
    try:
        with closing(connect_db()) as db:
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (email,))
                user_data = cursor.fetchone()
                if user_data:
                    columns = ['id', 'email', 'username', 'full_name', 'hashed_password']
                    return dict(zip(columns, user_data))
                return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None

# --- CONVERSATION & ASSESSMENT ---
def create_conversation(user_id, title="New Chat"):
    sql = "INSERT INTO conversations (user_id, title) VALUES (%s, %s) RETURNING id"
    with closing(connect_db()) as db:
        if db is None: return None
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id, title))
            new_id = cursor.fetchone()[0]
            db.commit()
    return new_id

def get_user_conversations(user_id):
    sql = "SELECT id, title, completion_score, video_url FROM conversations WHERE user_id = %s ORDER BY start_time DESC"
    with closing(connect_db()) as db:
        if db is None: return []
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            # fetchall() is safe to call even with 0 results, it will return []
            conversations = [{"id": row[0], "title": row[1], "completion_score": row[2], "video_url": row[3]} for row in cursor.fetchall()]
    return conversations

def update_conversation_score(conversation_id, score):
    sql = "UPDATE conversations SET completion_score = %s WHERE id = %s"
    with closing(connect_db()) as db:
        if db is None: return
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (score, conversation_id))
            db.commit()

def delete_conversation(conversation_id):
    sql = "DELETE FROM conversations WHERE id = %s"
    with closing(connect_db()) as db:
        if db is None: return False
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (conversation_id,))
            db.commit()
        return True

def clear_all_assessments(user_id):
    sql = "DELETE FROM conversations WHERE user_id = %s AND title LIKE 'PHQ-9 Assessment%%'"
    with closing(connect_db()) as db:
        if db is None: return False
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            db.commit()
        return True

# --- BEHAVIOUR LOGS ---
def save_behavior_log(user_id, date, hours_played, mood_score, solo_play_ratio, late_night_gaming, physical_breaks, social_interaction_score):
    sql = """
    INSERT INTO behavior_logs (user_id, log_date, hours_played, mood_score, solo_play_ratio, late_night_gaming, physical_breaks, social_interaction_score) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (user_id, log_date) DO UPDATE SET
        hours_played = EXCLUDED.hours_played, mood_score = EXCLUDED.mood_score, solo_play_ratio = EXCLUDED.solo_play_ratio,
        late_night_gaming = EXCLUDED.late_night_gaming, physical_breaks = EXCLUDED.physical_breaks, social_interaction_score = EXCLUDED.social_interaction_score;
    """
    with closing(connect_db()) as db:
        if db is None: return
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id, date, hours_played, mood_score, solo_play_ratio, late_night_gaming, physical_breaks, social_interaction_score))
            db.commit()

def get_behavior_logs(user_id):
    sql = "SELECT log_date, hours_played, mood_score, solo_play_ratio, late_night_gaming, physical_breaks, social_interaction_score FROM behavior_logs WHERE user_id = %s ORDER BY log_date DESC"
    with closing(connect_db()) as db:
        if db is None: return pd.DataFrame()
        df = pd.read_sql(sql, db, params=(user_id,))
        if not df.empty:
            df = df.rename(columns={"log_date": "date"})
    return df

# --- PHQ-9 & ASSESSMENT HELPERS ---
def get_latest_phq9(user_id):
    sql = """
        SELECT start_time, completion_score, answers 
        FROM conversations 
        WHERE user_id = %s AND completion_score IS NOT NULL AND title LIKE 'PHQ-9 Assessment%%' 
        ORDER BY start_time DESC LIMIT 1;
    """
    with closing(connect_db()) as db:
        if db is None: return None
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
    if not row:
        return None
    
    try:
        from shared import get_severity_for_score
        severity = get_severity_for_score(row[1])
    except (ImportError, AttributeError):
        severity = "Unknown"
        
    return {"date": row[0], "total_score": row[1], "severity_level": severity, "answers": row[2]}


def get_score_trend(user_id):
    sql = "SELECT completion_score FROM conversations WHERE user_id = %s AND completion_score IS NOT NULL AND title LIKE 'PHQ-9 Assessment%%' ORDER BY start_time DESC LIMIT 2;"
    with closing(connect_db()) as db:
        if db is None: return (None, None)
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            scores = [row[0] for row in cursor.fetchall()]
    if len(scores) == 2: return (scores[0], scores[1])
    elif len(scores) == 1: return (scores[0], None)
    else: return (None, None)

# --- EMOTION LOGS ---
def get_latest_emotion(user_id):
    sql = "SELECT emotion, date, probability, vader_compound FROM emotion_logs WHERE user_id = %s ORDER BY date DESC LIMIT 1;"
    with closing(connect_db()) as db:
        if db is None: return None
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
    return {"emotion": row[0], "date": row[1], "probability": row[2], "vader_compound": row[3]} if row else None

def save_emotion_log(user_id, date, emotion, probability, vader_compound):
    sql = "INSERT INTO emotion_logs (user_id, date, emotion, probability, vader_compound) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (user_id, date) DO UPDATE SET emotion = EXCLUDED.emotion, probability = EXCLUDED.probability, vader_compound = EXCLUDED.vader_compound;"
    with closing(connect_db()) as db:
        if db is None: return
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id, date, emotion, probability, vader_compound))
            db.commit()

def get_emotion_history(user_id):
    sql = "SELECT date, emotion, probability, vader_compound FROM emotion_logs WHERE user_id = %s ORDER BY date ASC"
    with closing(connect_db()) as db:
        if db is None: return []
        history = pd.read_sql(sql, db, params=(user_id,))
    return history.to_dict('records')

# --- CALENDAR & EVENTS ---
def save_calendar_events(user_id, events_to_save, is_generated):
    with closing(connect_db()) as db:
        if db is None: return False
        with closing(db.cursor()) as cursor:
            if is_generated:
                cursor.execute("DELETE FROM calendar_events WHERE user_id = %s AND is_generated = TRUE", (user_id,))
            sql_insert = "INSERT INTO calendar_events (user_id, title, start_time, end_time, color, is_generated) VALUES (%s, %s, %s, %s, %s, %s)"
            data_to_insert = [(user_id, e['title'], e['start'], e['end'], e.get('color', '#6f42c1'), is_generated) for e in events_to_save]
            psycopg2.extras.execute_batch(cursor, sql_insert, data_to_insert)
            db.commit()
    return True

def get_calendar_events(user_id):
    sql = "SELECT id, title, start_time, end_time, color, is_generated, completed, user_mood FROM calendar_events WHERE user_id = %s"
    events = []
    with closing(connect_db()) as db:
        if db is None: return []
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            for row in cursor.fetchall():
                events.append({"id": str(row[0]), "title": row[1], "start": row[2].isoformat(), "end": row[3].isoformat(), "color": row[4], "is_generated": row[5], "completed": row[6], "user_mood": row[7]})
    return events

def get_todays_events(user_id, today_date):
    start_of_day = datetime.combine(today_date, time.min)
    end_of_day = start_of_day + timedelta(days=1)
    sql = "SELECT title, start_time FROM calendar_events WHERE user_id = %s AND start_time >= %s AND start_time < %s ORDER BY start_time ASC;"
    try:
        with closing(connect_db()) as db:
            if db is None: return []
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (user_id, start_of_day, end_of_day))
                events = []
                for title, start_timestamp in cursor.fetchall():
                    events.append((title, start_timestamp.time()))
                return events
    except Exception as e:
        print(f"Error fetching today's events for user {user_id}: {e}")
        return []

#######Changed

def get_scores_over_time(user_id):
    """
    Fetches all completed assessment scores, timestamps, and detailed answers for a user.
    """
    sql = """
        SELECT start_time, completion_score, answers 
        FROM conversations 
        WHERE user_id = %s 
          AND completion_score IS NOT NULL 
          AND answers IS NOT NULL
          AND title LIKE 'PHQ-9 Assessment%%'
        ORDER BY start_time ASC;
    """
    with closing(connect_db()) as db:
        if db is None: return pd.DataFrame()
        
        # Use pandas to read directly from the SQL query for simplicity
        df = pd.read_sql(sql, db, params=(user_id,))
        if not df.empty:
            df = df.rename(columns={
                "start_time": "Date", 
                "completion_score": "Score",
                "answers": "Answers" # The 'answers' column will contain lists
            })
            df['Date'] = pd.to_datetime(df['Date']).dt.date
    return df