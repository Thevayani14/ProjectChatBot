import streamlit as st
import psycopg2
import psycopg2.extras
from contextlib import closing

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
        if 'db' in locals() and db:
            db.rollback()
        return False

def upsert_google_user(email, full_name, refresh_token):
    sql = """
        INSERT INTO users (email, full_name, refresh_token)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            refresh_token = EXCLUDED.refresh_token
        RETURNING id;
    """
    try:
        # This is the line that was fixed
        with closing(connect_db()) as db:
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (email, full_name, refresh_token))
                user_id = cursor.fetchone()[0]
            db.commit()
            return user_id
    except Exception as e:
        print(f"Error upserting Google user: {e}")
        if 'db' in locals() and db:
            db.rollback()
        return None

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

# --- ALL OTHER ASSESSMENT/CONVERSATION FUNCTIONS ---
# (create_conversation, get_user_conversations, add_message, get_messages, delete_conversation, update_conversation_score)
# ... paste all those functions here ...
