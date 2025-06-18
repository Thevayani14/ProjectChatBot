import streamlit as st
import psycopg2
from contextlib import closing
import re

# --- DATABASE CONNECTION ---
def connect_db():
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

# --- ALL OTHER FUNCTIONS (add_user, get_user, etc.) are unchanged ---
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

# --- THE FUNCTION WE ARE DEBUGGING ---
def get_latest_assessment_score(user_id):
    print(f"\n--- DEBUG: ENTERING get_latest_assessment_score for user_id: {user_id} ---")
    find_latest_conv_sql = """
        SELECT id FROM conversations
        WHERE user_id = %s AND title LIKE 'PHQ-9 Assessment%%'
        ORDER BY start_time DESC
        LIMIT 1
    """
    get_last_message_sql = """
        SELECT content FROM chat_history
        WHERE conversation_id = %s
        ORDER BY timestamp DESC
        LIMIT 1
    """
    try:
        with closing(connect_db()) as db:
            if db is None:
                print("--- DEBUG: DB connection failed. ---")
                return None
            with closing(db.cursor()) as cursor:
                cursor.execute(find_latest_conv_sql, (user_id,))
                result = cursor.fetchone()
                print(f"--- DEBUG: SQL to find latest assessment conversation returned: {result} ---")
                if not result:
                    print("--- DEBUG: No assessment conversations found. Exiting function. ---")
                    return None
                
                latest_conv_id = result[0]
                print(f"--- DEBUG: Found latest conversation ID: {latest_conv_id} ---")
                
                cursor.execute(get_last_message_sql, (latest_conv_id,))
                last_message_result = cursor.fetchone()
                print(f"--- DEBUG: SQL to find last message returned: {last_message_result} ---")
                if not last_message_result:
                    print(f"--- DEBUG: Conversation {latest_conv_id} is empty. Exiting function. ---")
                    return None
                
                last_message_content = last_message_result[0]
                print("--- DEBUG: The exact content of the last message is: ---")
                print(repr(last_message_content)) # Use repr() to show hidden characters
                print("---------------------------------------------------------")
                
                pattern = r"total PHQ-9 score is:\s*(\d+)/27"
                match = re.search(pattern, last_message_content, re.IGNORECASE)
                print(f"--- DEBUG: Regex match result: {match} ---")
                
                if match:
                    score = int(match.group(1))
                    print(f"--- DEBUG: SUCCESS! Parsed score: {score}. Exiting function. ---")
                    return score
                else:
                    print("--- DEBUG: Regex did not match. Exiting function. ---")
                    return None
                    
    except Exception as e:
        print(f"--- DEBUG: An exception occurred: {e} ---")
        return None

# --- SCHEDULE FUNCTIONS (unchanged) ---
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
