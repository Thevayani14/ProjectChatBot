import streamlit as st
import psycopg2
from contextlib import closing
import re # Import the regular expression module

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

# --- USER FUNCTIONS ---
def add_user(username, hashed_password):
    """Adds a new user to the database."""
    sql = "INSERT INTO users (username, hashed_password) VALUES (%s, %s)"
    try:
        with closing(connect_db()) as db:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (username, hashed_password))
            db.commit()
        return True
    except psycopg2.IntegrityError: # Username already exists
        return False

def get_user(username):
    """Retrieves a user's data from the database by username."""
    sql = "SELECT id, username, hashed_password FROM users WHERE username = %s"
    with closing(connect_db()) as db:
        if db is None: return None
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (username,))
            user_data = cursor.fetchone()
            if user_data:
                return {"id": user_data[0], "username": user_data[1], "hashed_password": user_data[2]}
            return None

# --- CONVERSATION & MESSAGE FUNCTIONS ---
def create_conversation(user_id, title="New Chat"):
    """Creates a new conversation for a user and returns its ID."""
    sql = "INSERT INTO conversations (user_id, title) VALUES (%s, %s) RETURNING id"
    with closing(connect_db()) as db:
        if db is None: return None
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id, title))
            new_id = cursor.fetchone()[0]
        db.commit()
        return new_id

def get_user_conversations(user_id):
    """Retrieves all conversations for a specific user, most recent first."""
    sql = "SELECT id, title, start_time FROM conversations WHERE user_id = %s ORDER BY start_time DESC"
    with closing(connect_db()) as db:
        if db is None: return []
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            results = cursor.fetchall()
            conversations = [{"id": row[0], "title": row[1], "start_time": str(row[2])} for row in results]
            return conversations

def update_conversation_title(conversation_id, title):
    """Updates the title of a specific conversation."""
    sql = "UPDATE conversations SET title = %s WHERE id = %s"
    with closing(connect_db()) as db:
        if db is None: return
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (title, conversation_id))
        db.commit()

def add_message(conversation_id, role, content):
    """Adds a chat message to a specific conversation."""
    sql = "INSERT INTO chat_history (conversation_id, role, content) VALUES (%s, %s, %s)"
    with closing(connect_db()) as db:
        if db is None: return
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (conversation_id, role, content))
        db.commit()

def get_messages(conversation_id):
    """Retrieves all messages for a specific conversation, ordered by timestamp."""
    sql = "SELECT role, content FROM chat_history WHERE conversation_id = %s ORDER BY timestamp ASC"
    with closing(connect_db()) as db:
        if db is None: return []
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (conversation_id,))
            messages = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
            return messages

def delete_conversation(conversation_id):
    """Deletes a single conversation and its associated messages by its ID."""
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

def get_latest_assessment_score(user_id):
    """
    Finds the latest completed assessment for a user and extracts the score.
    Returns the score as an integer, or None if not found.
    """
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
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(find_latest_conv_sql, (user_id,))
                result = cursor.fetchone()
                if not result:
                    return None
                
                latest_conv_id = result[0]
                
                cursor.execute(get_last_message_sql, (latest_conv_id,))
                last_message_result = cursor.fetchone()
                if not last_message_result:
                    return None
                
                last_message_content = last_message_result[0]
                
                match = re.search(r"score is: (\d+)/27", last_message_content)
                if match:
                    return int(match.group(1))
                else:
                    return None
                    
    except Exception as e:
        print(f"Error fetching latest assessment score for user {user_id}: {e}")
        return None
