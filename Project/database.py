import streamlit as st
import psycopg course. Here is the complete and final code for `database.py`.

This version2
import psycopg2.extras # Often useful, good to keep
from contextlib import closing

# --- DATABASE CONNECTION ---
 is designed to support the hybrid authentication model. It includes:
*   Functions to add both password-based users anddef connect_db():
    """
    Connects to the PostgreSQL database using credentials from st.secrets.
 Google OAuth users.
*   A single function `get_user_by_email` to retrieve any user type    Returns a connection object.
    """
    try:
        conn = psycopg2.connect(
            host=.
*   All the necessary functions for managing assessment conversations, messages, and scores.
*   It **removesst.secrets.database.host,
            port=st.secrets.database.port,
            dbname=st.secrets.database.dbname,
            user=st.secrets.database.user,
            password=** all the old code related to the `schedules` and `calendar_events` tables, as that logic is now handled byst.secrets.database.password
        )
        return conn
    except psycopg2.OperationalError as e the Google Calendar API.

Simply copy this entire block and replace the content of your `database.py` file.

---:
        st.error(f"Database connection failed: {e}")
        return None

# --- USER MANAGEMENT FUNCTIONS

### `database.py` (Complete and Final Code)

```python
import streamlit as st
import psycopg ---

def add_password_user(email, username, hashed_password, google_calendar_id):
    """2
from contextlib import closing

# --- DATABASE CONNECTION ---
def connect_db():
    """Connects
    Adds a new user who signed up with a password.
    Their full_name defaults to their chosen username.
     to the PostgreSQL database using credentials from st.secrets."""
    try:
        conn = psycopg2.connect("""
    sql = """
        INSERT INTO users (email, username, full_name, hashed_password,
            host=st.secrets.database.host, port=st.secrets.database.port,
            dbname google_calendar_id)
        VALUES (%s, %s, %s, %s, %s)=st.secrets.database.dbname, user=st.secrets.database.user,
            password=st
    """
    try:
        with closing(connect_db()) as db:
            if db is.secrets.database.password
        )
        return conn
    except psycopg2.OperationalError as e: None: return False
            with closing(db.cursor()) as cursor:
                # The user's display
        st.error(f"Database connection failed: {e}")
        return None

# --- USER MANAGEMENT FUNCTIONS ---

def add_password_user(email, username, hashed_password, google_calendar_id):
    """ name (full_name) defaults to their username upon creation
                cursor.execute(sql, (email, username, username, hashed_password, google_calendar_id))
            db.commit()
        return True
Adds a new user who signed up with a password."""
    # Note: We use the username as the full_name by    except Exception as e:
        print(f"Error creating password user with email {email}: {e}")
 default for password users.
    sql = """
        INSERT INTO users (email, username, full_name, hashed_password        # It's helpful to rollback on error
        if 'db' in locals() and db:
            db., google_calendar_id)
        VALUES (%s, %s, %s, %s, %srollback()
        return False

def upsert_google_user(email, full_name, refresh_token)
    """
    try:
        with closing(connect_db()) as db:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(sql):
    """
    Inserts a new user who signed in with Google or updates their tokens if they already exist.
    , (email, username, username, hashed_password, google_calendar_id))
            db.commit()The email is the unique conflict key.
    """
    sql = """
        INSERT INTO users (email, full
        return True
    except Exception as e:
        print(f"Error creating password user: {e}")
        _name, refresh_token)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            refresh_token# In case of an error, rollback changes
        if db:
            db.rollback()
        return False = EXCLUDED.refresh_token
        RETURNING id;
    """
    try:
        with closing(connect

def upsert_google_user(email, full_name, refresh_token):
    """
    Inserts a_db()) as db:
            if db is None: return None
            with closing(db.cursor()) new user who signed in with Google, or updates their tokens if they already exist.
    """
    sql = """
         as cursor:
                cursor.execute(sql, (email, full_name, refresh_token))
                user_id = cursor.fetchone()[0]
            db.commit()
            return user_id
    INSERT INTO users (email, full_name, refresh_token)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO UPDATE SET
            full_name = EXCLUDED.full_name,
except Exception as e:
        print(f"Error upserting Google user with email {email}: {e}")
        if 'db' in locals() and db:
            db.rollback()
        return None

            refresh_token = EXCLUDED.refresh_token
        RETURNING id;
    """
    try:
        def get_user_by_email(email):
    """
    Retrieves a user's complete data bywith closing(connect_db()) as db:
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (email, full_name, refresh_ their unique email address.
    This works for both password-based and Google-based users.
    """
    sqltoken))
                user_id = cursor.fetchone()[0]
            db.commit()
            return user = "SELECT id, email, username, full_name, hashed_password, refresh_token, google_calendar_id_id
    except Exception as e:
        print(f"Error upserting Google user: {e FROM users WHERE email = %s"
    try:
        with closing(connect_db()) as db:}")
        return None

def get_user_by_email(email):
    """
    Retrieves
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (email,))
                user_data = cursor.fetchone()
                if user_data a user's complete data from the database using their email.
    This works for both password-based and Google OAuth users.:
                    columns = ['id', 'email', 'username', 'full_name', 'hashed_password', 'refresh
    """
    sql = "SELECT id, email, username, full_name, hashed_password, refresh_token', 'google_calendar_id']
                    return dict(zip(columns, user_data))
_token, google_calendar_id FROM users WHERE email = %s"
    try:
        with closing                return None
    except Exception as e:
        print(f"Error getting user by email {email}:(connect_db()) as db:
            if db is None: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (email,))
                user_data = cursor. {e}")
        return None


# --- ASSESSMENT CONVERSATION & MESSAGE FUNCTIONS ---

def create_conversation(user_id, title="New Chat"):
    """Creates a new assessment conversation record."""
    sql = "INSERT INTO conversations (user_fetchone()
                if user_data:
                    # Map the tuple to a dictionary for easy access by name
                    columnsid, title) VALUES (%s, %s) RETURNING id"
    try:
        with closing( = ['id', 'email', 'username', 'full_name', 'hashed_password', 'refresh_tokenconnect_db()) as db:
            if db is None: return None
            with closing(db.cursor', 'google_calendar_id']
                    return dict(zip(columns, user_data))
                return None
    ()) as cursor:
                cursor.execute(sql, (user_id, title))
                new_idexcept Exception as e:
        print(f"Error getting user by email: {e}")
        return None = cursor.fetchone()[0]
            db.commit()
            return new_id
    except Exception as


# --- ASSESSMENT CONVERSATION & MESSAGE FUNCTIONS ---

def create_conversation(user_id, title="New e:
        print(f"Error creating conversation for user {user_id}: {e}")
        if Chat"):
    """Creates a new conversation record and returns its ID."""
    sql = "INSERT INTO conversations (user_id 'db' in locals() and db:
            db.rollback()
        return None

def get_user, title) VALUES (%s, %s) RETURNING id"
    with closing(connect_db()) as_conversations(user_id):
    """Retrieves all assessment conversations for a given user."""
    sql = "SELECT db:
        if db is None: return None
        with closing(db.cursor()) as cursor:
 id, title, start_time FROM conversations WHERE user_id = %s ORDER BY start_time DESC"
            cursor.execute(sql, (user_id, title))
            new_id = cursor.fetchone()[    with closing(connect_db()) as db:
        if db is None: return []
        with closing0]
        db.commit()
        return new_id

def get_user_conversations(user(db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            results_id):
    """Retrieves all conversations for a user to display in the history."""
    sql = "SELECT id, title, start_time FROM conversations WHERE user_id = %s ORDER BY start_time DESC"
     = cursor.fetchall()
            # Ensure start_time is converted to string for JSON compatibility in session state
            conversationswith closing(connect_db()) as db:
        if db is None: return []
        with closing( = [{"id": row[0], "title": row[1], "start_time": str(row[2])} for row in results]
            return conversations

def add_message(conversation_id, role,db.cursor()) as cursor:
            cursor.execute(sql, (user_id,))
            results = cursor.fetchall content):
    """Adds a single message to a conversation's chat history."""
    sql = "INSERT INTO chat_history()
            # Convert results to a list of dictionaries
            conversations = [{"id": row[0], "title": (conversation_id, role, content) VALUES (%s, %s, %s)"
    with closing( row[1], "start_time": str(row[2])} for row in results]
            return conversations

def add_message(conversation_id, role, content):
    """Adds a single chat message to aconnect_db()) as db:
        if db is None: return
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (conversation_id, role, content))
        db. conversation."""
    sql = "INSERT INTO chat_history (conversation_id, role, content) VALUES (%s,commit()

def get_messages(conversation_id):
    """Retrieves all messages for a given assessment conversation."""
 %s, %s)"
    with closing(connect_db()) as db:
        if db is None    sql = "SELECT role, content FROM chat_history WHERE conversation_id = %s ORDER BY timestamp ASC": return
        with closing(db.cursor()) as cursor:
            cursor.execute(sql, (conversation_id, role, content))
        db.commit()

def get_messages(conversation_id):

    with closing(connect_db()) as db:
        if db is None: return []
        with closing(db    """Retrieves all messages for a specific conversation."""
    sql = "SELECT role, content FROM chat_history WHERE conversation.cursor()) as cursor:
            cursor.execute(sql, (conversation_id,))
            messages = [{"_id = %s ORDER BY timestamp ASC"
    with closing(connect_db()) as db:
        role": row[0], "content": row[1]} for row in cursor.fetchall()]
            return messagesif db is None: return []
        with closing(db.cursor()) as cursor:
            cursor.execute

def delete_conversation(conversation_id):
    """Deletes a single conversation and all of its messages."""
    delete(sql, (conversation_id,))
            messages = [{"role": row[0], "content": row[_messages_sql = "DELETE FROM chat_history WHERE conversation_id = %s"
    delete_conversation1]} for row in cursor.fetchall()]
            return messages

def delete_conversation(conversation_id):
    """_sql = "DELETE FROM conversations WHERE id = %s"
    try:
        with closing(connect_Deletes a single conversation and all its messages."""
    delete_messages_sql = "DELETE FROM chat_history WHEREdb()) as db:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(delete_messages_sql, (conversation_id,))
                cursor.execute conversation_id = %s"
    delete_conversation_sql = "DELETE FROM conversations WHERE id = %s(delete_conversation_sql, (conversation_id,))
            db.commit()
        return True
    "
    try:
        with closing(connect_db()) as db:
            if db is None:except Exception as e:
        print(f"Error deleting conversation {conversation_id}: {e}")
         return False
            with closing(db.cursor()) as cursor:
                # Must delete messages first due to foreign key constraint
                cursor.execute(delete_messages_sql, (conversation_id,))
                cursor.executeif 'db' in locals() and db:
            db.rollback()
        return False

def update_conversation_(delete_conversation_sql, (conversation_id,))
            db.commit()
        return True
    score(conversation_id, score):
    """Updates a conversation with the final assessment score."""
    sql = "except Exception as e:
        print(f"Error deleting conversation {conversation_id}: {e}")
        UPDATE conversations SET completion_score = %s WHERE id = %s"
    try:
        with closing(return False

# --- ASSESSMENT SCORE FUNCTIONS ---
def update_conversation_score(conversation_id, score):
connect_db()) as db:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (score, conversation_id))
            db.commit    """Saves the final score of an assessment to its conversation record."""
    sql = "UPDATE conversations SET completion_score()
        return True
    except Exception as e:
        print(f"Error updating score for conversation { = %s WHERE id = %s"
    try:
        with closing(connect_db()) as dbconversation_id}: {e}")
        if 'db' in locals() and db:
            db.rollback:
            if db is None: return False
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (score, conversation_id))
            db.commit()
        return True
()
        return False

def get_latest_assessment_score(user_id):
    """Retrieves the score    except Exception as e:
        print(f"Error updating score for conversation {conversation_id}: {e from the most recently completed assessment for a user."""
    sql = """
        SELECT completion_score FROM conversations
        WHERE user_id = %s AND completion_score IS NOT NULL
        ORDER BY start_time DESC LIMIT 1
}")
        return False

def get_latest_assessment_score(user_id):
    """Retrieves the score from    """
    try:
        with closing(connect_db()) as db:
            if db is None the most recently completed assessment for a user."""
    sql = """
        SELECT completion_score FROM conversations
        WHERE user: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, (_id = %s AND completion_score IS NOT NULL
        ORDER BY start_time DESC LIMIT 1
    """
    try:
        with closing(connect_db()) as db:
            if db is Noneuser_id,))
                result = cursor.fetchone()
                return result[0] if result else None
    except Exception: return None
            with closing(db.cursor()) as cursor:
                cursor.execute(sql, ( as e:
        print(f"Error fetching latest score for user {user_id}: {e}")
        return None
```user_id,))
                result = cursor.fetchone()
                # fetchone() returns a tuple, e.
