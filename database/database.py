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

    # Activities Table (History Service)
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
    
    # Safe migration for new History Service columns
    for col, ctype in [
        ("action_type", "TEXT"),
        ("entity_type", "TEXT"),
        ("entity_id", "INTEGER"),
        ("payload_json", "TEXT")
    ]:
        try:
            cursor.execute(f"ALTER TABLE activities ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass

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

    # Knowledge Sources (Replaces documents)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL, 
            title TEXT NOT NULL,
            original_filename TEXT,
            source_path TEXT,
            url TEXT,
            raw_content TEXT,
            size INTEGER,
            project TEXT,
            category TEXT,
            simple_explanation TEXT,
            important_concepts TEXT,
            questions TEXT,
            learning_insights TEXT,
            action_items TEXT,
            difficulty_level TEXT,
            estimated_read_time INTEGER,
            knowledge_tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Knowledge Chunks (For RAG)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            chunk_index INTEGER,
            content TEXT,
            FOREIGN KEY(source_id) REFERENCES knowledge_sources(id)
        )
    ''')

    # Knowledge Chat History
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(source_id) REFERENCES knowledge_sources(id)
        )
    ''')

    # Image Studio History
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            style TEXT,
            aspect_ratio TEXT,
            model TEXT,
            quality TEXT,
            local_path TEXT NOT NULL,
            generation_type TEXT,
            width INTEGER,
            height INTEGER,
            generation_time REAL,
            seed TEXT,
            favorite INTEGER DEFAULT 0,
            reference_images TEXT,
            vision_prompt TEXT,
            generation_mode TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    for col, ctype in [
        ("reference_images", "TEXT"),
        ("vision_prompt", "TEXT"),
        ("generation_mode", "TEXT")
    ]:
        try:
            cursor.execute(f"ALTER TABLE image_history ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass


    for col, ctype in [
        ("status", "TEXT DEFAULT 'PENDING'"),
        ("summary", "TEXT"),
        ("key_points", "TEXT"),
        ("transcript", "TEXT"),
        ("suggested_questions", "TEXT"),
        ("raw_response", "TEXT"),
        ("video_id", "TEXT"),
        ("channel", "TEXT"),
        ("transcript_length", "INTEGER"),
        ("extraction_method", "TEXT"),
        ("processing_time", "REAL"),
        ("quotes", "TEXT"),
        ("chapters", "TEXT"),
        ("people_mentioned", "TEXT"),
        ("companies_mentioned", "TEXT"),
        ("topics", "TEXT"),
        ("content_hash", "TEXT")
    ]:
        try:
            cursor.execute(f"ALTER TABLE knowledge_sources ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass
            
    # Safe Migrations for knowledge_chunks
    for col, ctype in [
        ("embedding_json", "TEXT"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]:
        try:
            cursor.execute(f"ALTER TABLE knowledge_chunks ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass

    # Study Materials
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            material_type TEXT, 
            content_json TEXT,  
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(source_id) REFERENCES knowledge_sources(id)
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

    # Projects Table (Task Manager V3)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            color TEXT,
            icon TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Safe Migration for existing DB
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN progress INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        cursor.execute("ALTER TABLE chat_history ADD COLUMN role TEXT DEFAULT 'user'")
    except sqlite3.OperationalError:
        pass

    # Safe Migration for new Tasks V2 columns
    for col, ctype in [
        ("description", "TEXT"),
        ("category", "TEXT DEFAULT 'Work'"),
        ("estimated_time", "INTEGER DEFAULT 0"),
        ("actual_time", "INTEGER DEFAULT 0"),
        ("plan_id", "INTEGER"),
        ("source_type", "TEXT DEFAULT 'Manual'"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("due_time", "TEXT"),
        ("reminder", "TEXT"),
        ("repeat_rule", "TEXT"),
        ("project_id", "INTEGER"),
        ("ai_generated", "BOOLEAN DEFAULT 0"),
        ("goal_id", "INTEGER"),
        ("estimated_minutes", "INTEGER DEFAULT 0")
    ]:
        try:
            cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass

    # Subtasks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            position INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE subtasks ADD COLUMN sort_order INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Task Notes Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            content TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    ''')

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

    # Events Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            event_date TEXT,
            event_time TEXT,
            description TEXT,
            reminder_active BOOLEAN DEFAULT 1
        )
    ''')

    # Schedule History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_group_id TEXT NOT NULL,
            schedule_name TEXT NOT NULL,
            prompt TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Goals Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            target_date TIMESTAMP,
            progress INTEGER DEFAULT 0,
            status TEXT DEFAULT 'In Progress'
        )
    ''')

    # Chat Sessions Table (New AI Architecture)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Chat Messages Table (New AI Architecture)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
        )
    ''')

    # Safe Migration for existing DB
    try:
        cursor.execute("ALTER TABLE chat_sessions ADD COLUMN title TEXT DEFAULT 'New Conversation'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE chat_sessions ADD COLUMN custom_title TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE chat_sessions ADD COLUMN updated_at TIMESTAMP")
        # Backfill existing rows
        cursor.execute("UPDATE chat_sessions SET updated_at = created_at WHERE updated_at IS NULL")
    except sqlite3.OperationalError:
        pass

    # Plans Table (AI Planner V2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            goal TEXT,
            plan_type TEXT,
            status TEXT DEFAULT 'New',
            timeline_json TEXT,
            steps_json TEXT,
            resources_json TEXT,
            progress INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Plan Versions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS plan_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            roadmap_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES plans(id)
        )
    ''')

    try:
        cursor.execute("ALTER TABLE plans ADD COLUMN insights_json TEXT")
    except sqlite3.OperationalError:
        pass

    # Safe Migration for new Calendar V2 columns in events
    for col, ctype in [
        ("start_time", "TIMESTAMP"),
        ("end_time", "TIMESTAMP"),
        ("event_type", "TEXT DEFAULT 'event'"),
        ("priority", "TEXT DEFAULT 'Medium'"),
        ("category", "TEXT DEFAULT 'Personal'"),
        ("duration_minutes", "INTEGER DEFAULT 60"),
        ("ai_generated", "BOOLEAN DEFAULT 0"),
        ("schedule_group_id", "TEXT"),
        ("status", "TEXT DEFAULT 'Scheduled'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE events ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass
            
    # Backfill start_time and end_time for older events if needed
    try:
        # Assuming event_time is "HH:MM", we can approximate start_time
        cursor.execute("UPDATE events SET start_time = event_date || ' ' || event_time || ':00' WHERE start_time IS NULL AND event_date IS NOT NULL AND event_time IS NOT NULL")
        cursor.execute("UPDATE events SET start_time = event_date || ' 00:00:00' WHERE start_time IS NULL AND event_date IS NOT NULL AND event_time IS NULL")
        cursor.execute("UPDATE events SET end_time = start_time WHERE end_time IS NULL AND start_time IS NOT NULL")
    except Exception as e:
        print(f"Calendar V2 Backfill Warning: {e}")

    # No seed/mock data — all data is entered by real users

    # Task Manager V3 Performance Indexes
    indexes = [
        ("idx_tasks_title", "tasks (title)"),
        ("idx_tasks_status", "tasks (status)"),
        ("idx_tasks_priority", "tasks (priority)"),
        ("idx_tasks_due_date", "tasks (due_date)"),
        ("idx_tasks_project_id", "tasks (project_id)"),
        ("idx_subtasks_task_id", "subtasks (task_id)")
    ]
    for idx_name, idx_def in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()

# Initialize database schema
init_db()
