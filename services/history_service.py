import json
from database.database import get_connection
from services.event_bus import bus

def log_activity(user_id: int, activity_type: str, description: str, action_type: str = None, entity_type: str = None, entity_id: int = None, payload_json: str = None):
    """Logs a user activity with extended metadata for audit and analytics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if isinstance(payload_json, dict):
        payload_json = json.dumps(payload_json)
        
    cursor.execute('''
        INSERT INTO activities (user_id, activity_type, description, action_type, entity_type, entity_id, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, activity_type, description, action_type, entity_type, entity_id, payload_json))
    conn.commit()
    conn.close()
    
    # Trigger live update for UI
    bus.publish("ACTIVITY_ADDED", {})

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

def get_recent_activity(user_id: int, limit: int = 10):
    """
    Returns a normalized list of recent activities from across the system.
    Returns: list of dicts with keys: source, icon, title, summary, timestamp.
    """
    conn = get_connection()
    cursor = conn.cursor()
    activities = []

    # 1. Documents
    cursor.execute('SELECT title, summary, created_at FROM documents ORDER BY created_at DESC LIMIT ?', (limit,))
    for row in cursor.fetchall():
        activities.append({
            "source": "Notes & Docs",
            "icon": "📝",
            "title": row["title"],
            "summary": row["summary"] or "No summary",
            "timestamp": row["created_at"]
        })

    # 2. Tasks
    cursor.execute('SELECT title, status, due_date FROM tasks WHERE user_id = ? ORDER BY id DESC LIMIT ?', (user_id, limit))
    for row in cursor.fetchall():
        activities.append({
            "source": "Task Manager",
            "icon": "✅",
            "title": row["title"],
            "summary": f"Status: {row['status']}",
            "timestamp": row["due_date"] or "2026-01-01 00:00:00" # Fallback
        })

    # 3. Calendar Events
    cursor.execute('SELECT title, description, event_date, event_time FROM events ORDER BY id DESC LIMIT ?', (limit,))
    for row in cursor.fetchall():
        dt = f"{row['event_date']} {row['event_time']}" if row['event_date'] else "2026-01-01 00:00:00"
        activities.append({
            "source": "Calendar",
            "icon": "📅",
            "title": row["title"],
            "summary": (row["description"][:30] + '...') if row["description"] else "Scheduled Event",
            "timestamp": dt
        })

    # 4. Goals
    cursor.execute('SELECT title, progress, status, target_date FROM goals WHERE user_id = ? ORDER BY id DESC LIMIT ?', (user_id, limit))
    for row in cursor.fetchall():
        activities.append({
            "source": "Goal Tracker",
            "icon": "🏆",
            "title": row["title"],
            "summary": f"Progress: {row['progress']}% - {row['status']}",
            "timestamp": row["target_date"] or "2026-01-01 00:00:00"
        })

    # 5. AI Chat Sessions
    cursor.execute('SELECT session_id, created_at FROM chat_sessions ORDER BY created_at DESC LIMIT ?', (limit,))
    for row in cursor.fetchall():
        # Get last message
        cursor.execute('SELECT message FROM chat_messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1', (row["session_id"],))
        last_msg = cursor.fetchone()
        msg_text = last_msg["message"] if last_msg else "New Session"
        activities.append({
            "source": "Aurex AI",
            "icon": "🤖",
            "title": f"Session {row['session_id'][:8]}...",
            "summary": (msg_text[:30] + '...') if len(msg_text) > 30 else msg_text,
            "timestamp": row["created_at"]
        })

    conn.close()

    # Sort all gathered activities by timestamp DESC
    try:
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
    except Exception:
        pass # If timestamp parsing fails, just return as is

    return activities[:limit]

def clear_history(user_id: int):
    """Clears all history for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM activities WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user_id,))
    # Also clear the new AI architecture chat tables
    cursor.execute('DELETE FROM chat_messages')
    cursor.execute('DELETE FROM chat_sessions')
    # Also clear image history
    cursor.execute('DELETE FROM image_history WHERE user_id = ?', (user_id,))
    # Clear plans history
    cursor.execute('DELETE FROM plan_versions WHERE plan_id IN (SELECT id FROM plans WHERE user_id = ?)', (user_id,))
    cursor.execute('DELETE FROM plans WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    
    # Notify dashboard and other views to update
    bus.publish("HISTORY_UPDATED", {})
