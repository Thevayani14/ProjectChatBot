import streamlit as st
import psycopg2
from contextlib import closing

# --- DATABASE CONNECTION ---
def connect_db():
    """
    Connects to the PostgreSQL database using credentials from st.secrets.
    Returns a connection object.
    """
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
def add_password_user(email, username, hashed_password, google_calendar_id):
    """Adds a new user who signed up with a password."""
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
        print(f"Error creating password user with email {email}: {e}")
        if 'db' in locals() and db: db.rollback()
        return False

def upsert_google_user(email, full_name, refresh_token):
    """
    Inserts a new user who signed in with Google, or updates their tokens if they already exist.
    The email is the unique conflict key.
    """
    sql = """
        INSERT INTO users (email, full_name, refresh_token)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            refresh_token = EXCLUDED.refresh_token
        RETURNING id;
    """
    try:
        with closing(connect_db()) as db:
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (email, full_name, refresh_token))
                user_id = cursor.fetchone()[0]
            db.commit()
            return user_id
    except Exception as e:
        print(f"Error upserting Google user with email {email}: {e}")
        if 'db' in locals() and db: db.rollback()
        return None

def get_user_by_email(email):
    """
    Retrieves a user's complete data by their unique email address.
    This works for both password-based and Google-based users.
    """
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
        print(f"Error getting user by email {email}: {e}")
        return None

def save_google_calendar_id(user_id, calendar_id):
    """Saves the app-managed Google Calendar ID for a password-based user."""
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
                # result will be a tuple like ('calendar_id_string',) or None
                return result[0] if result and result[0] else None
    except Exception as e:
        print(f"Error fetching google_calendar_id for user {user_id}: {e}")
        return None

# --- ASSESSMENT CONVERSATION & MESSAGE FUNCTIONS ---
def create_conversation(user_id, title="New Chat"):
    """Creates a new assessment conversation record and returns its ID."""
    sql = "INSERT INTO conversations (user_id, title) VALUES (%s, %s) RETURNING id"
    try:
        with closing(connect_db()) as db:
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (user_id, title))
                new_id = cursor.fetchone()[0]
            db.commit()
            return new_id
    except Exception as e:
        print(f"Error creating conversation for user {user_id}: {e}")
        if 'db' in locals() and db: db.rollback()
        return None

def get_user_conversations(user_id):
    """Retrieves all assessment conversations for a given user."""
    sql = "SELECT id, title, start_time FROM conversations WHERE user_id = %s ORDER BY start_time DESC"
    try:
        with closing(connect_db()) as db:
            if db is None: return []
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (user_id,))
                results = cursor.fetchall()
                # Ensure start_time is converted to string for JSON compatibility in session state
                return [{"id": row[0], "title": row[1], "start_time": str(row[2])} for row in results]
    except Exception as e:
        print(f"Error getting conversations for user {user_id}: {e}")
        return []

def add_message(conversation_id, role, content):
    """Adds a single message to a conversation's chat history."""
    sql = "INSERT INTO chat_history (conversation_id, role, content) VALUES (%s, %s, %s)"
    try:
        with closing(connect_db()) as db:
            if db is None: return
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (conversation_id, role, content))
            db.commit()
    except Exception as e:
        print(f"Error adding message to conversation {conversation_id}: {e}")
        if 'db' in locals() and db: db.rollback()

def get_messages(conversation_id):
    """Retrieves all messages for a given assessment conversation."""
    sql = "SELECT role, content FROM chat_history WHERE conversation_id = %s ORDER BY timestamp ASC"
    try:
        with closing(connect_db()) as db:
            if db is None: return []
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (conversation_id,))
                return [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting messages for conversation {conversation_id}: {e}")
        return []

def delete_conversation(conversation_id):
    """Deletes a single conversation and all of its messages."""
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
        if 'db' in locals() and db: db.rollback()
        return False

def update_conversation_score(conversation_id, score):
    """Updates a conversation with the final assessment score."""
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
        if 'db' in locals() and db: db.rollback()
        return False

def get_latest_assessment_score(user_id):
    """Retrieves the score from the most recently completed assessment for a user."""
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
