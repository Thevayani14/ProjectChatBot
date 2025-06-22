import streamlit as st
import psycopg2
from contextlib import closing

# --- DATABASE CONNECTION ---
def connect_db():
    try:
        conn = psycopg2.connect(
            host=st.secrets.database.host, port=st.secrets.database.port,
            dbname=st.secrets.database.dbname, user=st.secrets.database.user,
            password=st.secrets.database.password
        )
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Database connection failed: {e}")
        return None

# --- USER MANAGEMENT FUNCTIONS ---
def add_password_user(email, username, hashed_password, google_calendar_id):
    sql = """
        INSERT INTO users (email, username, full_name, hashed_password, google_calendar_id)
        VALUES (%s, %s, %s, %s, %s)
    """
    try:
        with closing(connect_db()) as db:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (email, username, username, hashed_password, google_calendar_id))
            db.commit()
        return True
    except Exception as e:
        print(f"Error creating password user: {e}")
        if 'db' in locals() and db: db.rollback()
        return False

def upsert_google_user(email, full_name, refresh_token):
    sql = """
        INSERT INTO users (email, full_name, refresh_token, username)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            refresh_token = EXCLUDED.refresh_token
    """
    try:
        with closing(connect_db()) as db:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (email, full_name, refresh_token, email.split('@')[0]))
            db.commit()
        return True
    except Exception as e:
        print(f"Error upserting Google user: {e}")
        if 'db' in locals() and db: db.rollback()
        return False

def get_user_by_email(email):
    sql = "SELECT id, email, username, full_name, hashed_password, refresh_token, google_calendar_id FROM users WHERE email = %s"
    try:
        with closing(connect_db()) as db:
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (email,))
                user_data = cursor.fetchone()
                if user_data:
                    columns = ['id', 'email', 'username', 'full_name', 'hashed_password', 'refresh_token', 'google_calendar_id']
                    return dict(zip(columns, user_data))
                return None
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None

def save_google_calendar_id(user_id, calendar_id):
    sql = "UPDATE users SET google_calendar_id = %s WHERE id = %s"
    try:
        with closing(connect_db()) as db:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (calendar_id, user_id))
            db.commit()
        return True
    except Exception as e:
        print(f"Error saving calendar ID for user {user_id}: {e}")
        return False

def get_google_calendar_id(user_id):
    """Retrieves the app-managed Google Calendar ID for a password-based user."""
    sql = "SELECT google_calendar_id FROM users WHERE id = %s"
    try:
        with closing(connect_db()) as db:
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()
                return result[0] if result and result[0] else None
    except Exception as e:
        print(f"Error fetching google_calendar_id for user {user_id}: {e}")
        return None

# --- ASSESSMENT CONVERSATION & MESSAGE FUNCTIONS ---
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
    sql = "SELECT id, title, start_time FROM conversations WHERE user_id = %s ORDER BY start_time DESC"
    with closing(connect_db()) as db:
        if db is None: return []
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            results = cursor.fetchall()
            return [{"id": row[0], "title": row[1], "start_time": str(row[2])} for row in results]

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
            return [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]

def delete_conversation(conversation_id):
    delete_messages_sql = "DELETE FROM chat_history WHERE conversation_id = %s"
    delete_conversation_sql = "DELETE FROM conversations WHERE id = %s"
    try:
        with closing(connect_db()) as db:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(delete_messages_sql, (conversation_id,))
                cursor.execute(delete_conversation_sql, (conversation_id,))
            db.commit()
        return True
    except Exception as e:
        print(f"Error deleting conversation {conversation_id}: {e}")
        return False

def update_conversation_score(conversation_id, score):
    sql = "UPDATE conversations SET completion_score = %s WHERE id = %s"
    try:
        with closing(connect_db()) as db:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (score, conversation_id))
            db.commit()
        return True
    except Exception as e:
        print(f"Error updating score for conversation {conversation_id}: {e}")
        return False

def get_latest_assessment_score(user_id):
    sql = """
        SELECT completion_score FROM conversations
        WHERE user_id = %s AND completion_score IS NOT NULL
        ORDER BY start_time DESC LIMIT 1
    """
    try:
        with closing(connect_db()) as db:
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()
                return result[0] if result else None
    except Exception as e:
        print(f"Error fetching latest score for user {user_id}: {e}")
        return None
