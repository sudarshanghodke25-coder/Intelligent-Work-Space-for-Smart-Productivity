import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "users.db"

def get_connection():
    """Returns a connection to the SQLite database."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            profile_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Activities Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            description TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Sessions Table (Token Persistence)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Chat History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Documents Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_type TEXT NOT NULL,
            raw_content TEXT NOT NULL,
            summary TEXT,
            key_points TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tasks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            priority TEXT NOT NULL,
            due_date TIMESTAMP,
            progress INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pending'
        )
    ''')

    # Safe Migration for existing DB
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN progress INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Column already exists

    # Schedules Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            start_time TIMESTAMP,
            end_time TIMESTAMP
        )
    ''')

    # Focus Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS focus_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            tag TEXT NOT NULL,
            duration_minutes INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Inject Mock Data if empty
    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        from datetime import datetime, timedelta
        import random
        now = datetime.now()
        
        # Mock Tasks (One High priority < 24hrs to trigger Rule B)
        tasks = [
            (1, "Finalize Q3 Report", "High", (now + timedelta(hours=10)).strftime("%Y-%m-%d %H:%M:%S"), "Pending"),
            (1, "Review PRs", "Medium", (now + timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"), "Pending"),
            (1, "Design System Update", "Low", (now + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"), "Pending"),
        ]
        cursor.executemany("INSERT INTO tasks (user_id, title, priority, due_date, status) VALUES (?, ?, ?, ?, ?)", tasks)
        
        # Mock Schedules (Creating a 100-minute gap to trigger Rule A)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        schedules = [
            (1, "Daily Standup", "Meeting", (today + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S"), (today + timedelta(hours=9, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")),
            # 9:45 AM to 11:25 AM is 100 minutes (Gap > 90 mins)
            (1, "Deep Work", "Work", (today + timedelta(hours=11, minutes=25)).strftime("%Y-%m-%d %H:%M:%S"), (today + timedelta(hours=13, minutes=25)).strftime("%Y-%m-%d %H:%M:%S")),
        ]
        cursor.executemany("INSERT INTO schedules (user_id, title, category, start_time, end_time) VALUES (?, ?, ?, ?, ?)", schedules)
        
        # Mock Focus Logs
        logs = []
        for i in range(7):
            log_date = today - timedelta(days=6-i)
            logs.append((1, "Work", random.randint(30, 120), log_date.strftime("%Y-%m-%d %H:%M:%S")))
            logs.append((1, "Meeting", random.randint(10, 45), log_date.strftime("%Y-%m-%d %H:%M:%S")))
        cursor.executemany("INSERT INTO focus_logs (user_id, tag, duration_minutes, timestamp) VALUES (?, ?, ?, ?)", logs)

    conn.commit()
    conn.close()

# Initialize database schema
init_db()
