import streamlit as st
import psycopg2
from contextlib import closing
import re

# --- DATABASE CONNECTION (Unchanged) ---
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

# --- USER & CONVERSATION FUNCTIONS (Unchanged) ---
def add_user(username, hashed_password):
    sql = "INSERT INTO users (username, hashed_password) VALUES (%s, %s)"
    try:
        with closing(connect_db()) as db:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (username, hashed_password))
            db.commit()
        return True
    except psycopg2.IntegrityError:
        return False

def get_user(username):
    sql = "SELECT id, username, hashed_password FROM users WHERE username = %s"
    with closing(connect_db()) as db:
        if db is None: return None
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (username,))
            user_data = cursor.fetchone()
            if user_data:
                return {"id": user_data[0], "username": user_data[1], "hashed_password": user_data[2]}
            return None

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
            conversations = [{"id": row[0], "title": row[1], "start_time": str(row[2])} for row in results]
            return conversations

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

# --- NEW & UPDATED FUNCTIONS ---

def update_conversation_score(conversation_id, score):
    """Updates the conversation with the final assessment score."""
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
    """
    Retrieves the score from the most recent completed assessment.
    This is now 100% reliable as it reads from a dedicated column.
    """
    sql = """
        SELECT completion_score FROM conversations
        WHERE user_id = %s
          AND completion_score IS NOT NULL
        ORDER BY start_time DESC
        LIMIT 1
    """
    try:
        with closing(connect_db()) as db:
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()
                # fetchone() returns a tuple, e.g., (15,). We want the first element.
                return result[0] if result else None
    except Exception as e:
        print(f"Error fetching latest assessment score for user {user_id}: {e}")
        return None

# --- SCHEDULE FUNCTIONS (Unchanged) ---
def save_schedule(user_id, schedule_markdown):
    delete_sql = "DELETE FROM schedules WHERE user_id = %s"
    insert_sql = "INSERT INTO schedules (user_id, schedule_markdown) VALUES (%s, %s)"
    try:
        with closing(connect_db()) as db:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(delete_sql, (user_id,))
                cursor.execute(insert_sql, (user_id, schedule_markdown))
            db.commit()
        return True
    except Exception as e:
        print(f"Error saving schedule for user {user_id}: {e}")
        return False

def get_latest_schedule(user_id):
    sql = "SELECT schedule_markdown FROM schedules WHERE user_id = %s ORDER BY created_at DESC LIMIT 1"
    with closing(connect_db()) as db:
        if db is None: return None
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return None
