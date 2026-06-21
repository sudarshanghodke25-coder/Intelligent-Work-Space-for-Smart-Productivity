import bcrypt
import sqlite3
import uuid
import json
import os
from datetime import datetime, timedelta
from database.database import get_connection
from authentication.session import current_session
from services.history_service import log_activity

SESSION_FILE = ".aurex_session.json"

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    """Check a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def signup_user(full_name, email, username, password):
    """Registers a new user."""
    conn = get_connection()
    cursor = conn.cursor()
    
    hashed_password = hash_password(password)
    
    try:
        cursor.execute('''
            INSERT INTO users (full_name, email, username, password_hash)
            VALUES (?, ?, ?, ?)
        ''', (full_name, email, username, hashed_password))
        conn.commit()
        return True, "User registered successfully."
    except sqlite3.IntegrityError as e:
        if "email" in str(e).lower():
            return False, "An account with this email address already exists."
        elif "username" in str(e).lower():
            return False, "Username already exists."
        else:
            return False, "A database error occurred."
    finally:
        conn.close()

def login_user(email, password, remember_me=False):
    """Logs in a user and starts a session."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, full_name, username, email, password_hash FROM users
        WHERE email = ?
    ''', (email,))
    
    user = cursor.fetchone()
    
    if user and check_password(password, user["password_hash"]):
        login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_session.login(
            user_id=user["id"],
            username=user["username"],
            email=user["email"],
            full_name=user["full_name"],
            login_time=login_time
        )
        log_activity(user["id"], "Login", f"User {user['username']} logged in")
        
        token_str = ""
        if remember_me:
            token = str(uuid.uuid4())
            expires = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user["id"], expires))
            token_str = token
        
        # Save profile locally
        profile_data = {
            "email": user["email"],
            "full_name": user["full_name"],
            "token": token_str
        }
        with open(SESSION_FILE, "w") as f:
            json.dump(profile_data, f)
            
        conn.commit()
        conn.close()
        return True, "Login successful."
    else:
        conn.close()
        return False, "Invalid email or password."

def check_active_session():
    """Checks for a valid session token and returns (has_profile, auto_login, profile_data)"""
    if not os.path.exists(SESSION_FILE):
        return False, False, {}
        
    try:
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
    except:
        return False, False, {}
        
    email = data.get("email")
    token = data.get("token")
    if not email:
        return False, False, {}
        
    if not token:
        return True, False, data
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.id, u.full_name, u.username, u.email, s.expires_at 
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
    ''', (token,))
    
    session_row = cursor.fetchone()
    conn.close()
    
    if session_row:
        expires = datetime.strptime(session_row["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < expires:
            # Token valid, auto login
            current_session.login(
                user_id=session_row["id"],
                username=session_row["username"],
                email=session_row["email"],
                full_name=session_row["full_name"],
                login_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            return True, True, data
            
    # Token expired or invalid
    return True, False, data

def logout_user():
    """Logs out user, invalidates token in DB, but keeps profile local."""
    if current_session.is_logged_in():
        log_activity(current_session.user_id, "Logout", "User logged out")
        
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    data = json.load(f)
                if data.get("token"):
                    conn = get_connection()
                    conn.execute("DELETE FROM sessions WHERE token = ?", (data["token"],))
                    conn.commit()
                    conn.close()
                data["token"] = ""
                with open(SESSION_FILE, "w") as f:
                    json.dump(data, f)
            except:
                pass
                
    current_session.logout()

def clear_saved_profile():
    """Completely wipes local saved profile data (Switch Account)."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
