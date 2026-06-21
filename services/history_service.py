from database.database import get_connection

def log_activity(user_id: int, activity_type: str, description: str):
    """Logs a user activity."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO activities (user_id, activity_type, description)
        VALUES (?, ?, ?)
    ''', (user_id, activity_type, description))
    conn.commit()
    conn.close()

def get_recent_activities(user_id: int, limit: int = 20):
    """Fetches recent activities for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT activity_type, description, timestamp
        FROM activities
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def clear_history(user_id: int):
    """Clears all history for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM activities WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
