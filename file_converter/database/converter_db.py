"""
file_converter/database/converter_db.py
SQLite persistence layer for the File Converter module.
All tables are created via safe CREATE IF NOT EXISTS + ALTER migrations.
Connects to the same users.db as the rest of FLOWSPACE.
"""


from datetime import date
from pathlib import Path
from typing import List, Optional

from database.database import get_connection
from file_converter.models.conversion_history import HistoryEntry, ConverterStats


# ── Schema migration ────────────────────────────────────────────────────────

def init_converter_tables() -> None:
    """
    Create all File Converter tables in the shared FLOWSPACE database.
    Safe to call multiple times — uses CREATE IF NOT EXISTS and ALTER guards.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Main history table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS converter_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 1,
            job_id          TEXT NOT NULL,
            source_name     TEXT NOT NULL,
            source_ext      TEXT NOT NULL,
            target_ext      TEXT NOT NULL,
            source_size     INTEGER DEFAULT 0,
            output_path     TEXT DEFAULT '',
            status          TEXT NOT NULL DEFAULT 'PENDING',
            error_message   TEXT DEFAULT '',
            duration_ms     INTEGER DEFAULT 0,
            quality         TEXT DEFAULT 'High',
            ai_suggestion   TEXT DEFAULT '',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at    TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Key-value settings per user
    cur.execute("""
        CREATE TABLE IF NOT EXISTS converter_settings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL DEFAULT 1,
            key         TEXT NOT NULL,
            value       TEXT NOT NULL,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, key)
        )
    """)

    # Favorite tool IDs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS converter_favorite_tools (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL DEFAULT 1,
            tool_id     TEXT NOT NULL,
            pinned_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, tool_id)
        )
    """)

    # Pinned output files
    cur.execute("""
        CREATE TABLE IF NOT EXISTS converter_pinned (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL DEFAULT 1,
            file_path   TEXT NOT NULL,
            label       TEXT DEFAULT '',
            pinned_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, file_path)
        )
    """)

    # Conversion presets
    cur.execute("""
        CREATE TABLE IF NOT EXISTS converter_presets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL DEFAULT 1,
            name        TEXT NOT NULL,
            settings_json TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Persistent conversion log (verbose, for diagnostics)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS converter_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id      TEXT NOT NULL,
            level       TEXT NOT NULL DEFAULT 'INFO',
            message     TEXT NOT NULL,
            logged_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ── History CRUD ────────────────────────────────────────────────────────────

def insert_history(
    user_id: int,
    job_id: str,
    source_name: str,
    source_ext: str,
    target_ext: str,
    source_size: int,
    output_path: str,
    status: str,
    error_message: str,
    duration_ms: int,
    quality: str,
    ai_suggestion: str,
) -> int:
    """Insert a completed job into converter_history. Returns new row id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO converter_history
            (user_id, job_id, source_name, source_ext, target_ext,
             source_size, output_path, status, error_message,
             duration_ms, quality, ai_suggestion, completed_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?, CURRENT_TIMESTAMP)
    """, (
        user_id, job_id, source_name, source_ext, target_ext,
        source_size, output_path, status, error_message,
        duration_ms, quality, ai_suggestion,
    ))
    row_id = cur.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_history(
    user_id: int,
    limit: int = 50,
    status_filter: Optional[str] = None,
    search_query: str = "",
) -> List[HistoryEntry]:
    """Fetch history entries for the given user, newest first."""
    conn = get_connection()
    clauses = ["user_id = ?"]
    params: list = [user_id]

    if status_filter and status_filter != "All":
        clauses.append("status = ?")
        params.append(status_filter)

    if search_query:
        clauses.append("(source_name LIKE ? OR target_ext LIKE ?)")
        like = f"%{search_query}%"
        params.extend([like, like])

    where = " AND ".join(clauses)
    rows = conn.execute(
        f"SELECT * FROM converter_history WHERE {where} ORDER BY id DESC LIMIT ?",
        params + [limit],
    ).fetchall()
    conn.close()
    return [HistoryEntry.from_row(r) for r in rows]


def delete_history_entry(entry_id: int) -> None:
    """Hard-delete a single history row."""
    conn = get_connection()
    conn.execute("DELETE FROM converter_history WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


def clear_history(user_id: int = 1) -> None:
    """Hard-delete all history rows for a user."""
    conn = get_connection()
    conn.execute("DELETE FROM converter_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_stats(user_id: int) -> ConverterStats:
    """Compute aggregated stats for the right sidebar."""
    conn = get_connection()

    total = conn.execute(
        "SELECT COUNT(*) FROM converter_history WHERE user_id=?", (user_id,)
    ).fetchone()[0]
    success = conn.execute(
        "SELECT COUNT(*) FROM converter_history WHERE user_id=? AND status='COMPLETED'",
        (user_id,)
    ).fetchone()[0]
    failed = conn.execute(
        "SELECT COUNT(*) FROM converter_history WHERE user_id=? AND status='FAILED'",
        (user_id,)
    ).fetchone()[0]
    total_bytes = conn.execute(
        "SELECT COALESCE(SUM(source_size),0) FROM converter_history WHERE user_id=?",
        (user_id,)
    ).fetchone()[0]
    avg_dur = conn.execute(
        "SELECT COALESCE(AVG(duration_ms),0) FROM converter_history WHERE user_id=? AND status='COMPLETED'",
        (user_id,)
    ).fetchone()[0]

    popular_row = conn.execute("""
        SELECT target_ext, COUNT(*) as cnt
        FROM converter_history WHERE user_id=?
        GROUP BY target_ext ORDER BY cnt DESC LIMIT 1
    """, (user_id,)).fetchone()
    most_used = popular_row["target_ext"] if popular_row else ""

    today_str = date.today().isoformat()
    today_count = conn.execute(
        "SELECT COUNT(*) FROM converter_history WHERE user_id=? AND date(created_at)=?",
        (user_id, today_str)
    ).fetchone()[0]

    conn.close()
    return ConverterStats(
        total_conversions=total,
        successful=success,
        failed=failed,
        total_bytes_processed=total_bytes,
        avg_duration_ms=avg_dur,
        most_used_format=most_used,
        today_count=today_count,
    )


# ── Settings CRUD ───────────────────────────────────────────────────────────

def save_setting(user_id: int, key: str, value: str) -> None:
    conn = get_connection()
    conn.execute("""
        INSERT INTO converter_settings (user_id, key, value, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
    """, (user_id, key, value))
    conn.commit()
    conn.close()


def load_setting(user_id: int, key: str, default: str = "") -> str:
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM converter_settings WHERE user_id=? AND key=?",
        (user_id, key)
    ).fetchone()
    conn.close()
    return row["value"] if row else default


def load_all_settings(user_id: int) -> dict:
    conn = get_connection()
    rows = conn.execute(
        "SELECT key, value FROM converter_settings WHERE user_id=?", (user_id,)
    ).fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


# ── Favorite Tools ──────────────────────────────────────────────────────────

def get_favorite_tools(user_id: int) -> List[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT tool_id FROM converter_favorite_tools WHERE user_id=? ORDER BY pinned_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [r["tool_id"] for r in rows]


def toggle_favorite_tool(user_id: int, tool_id: str) -> bool:
    """Toggle a tool's favorite state. Returns True if now favorited."""
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM converter_favorite_tools WHERE user_id=? AND tool_id=?",
        (user_id, tool_id)
    ).fetchone()
    if existing:
        conn.execute(
            "DELETE FROM converter_favorite_tools WHERE user_id=? AND tool_id=?",
            (user_id, tool_id)
        )
        conn.commit()
        conn.close()
        return False
    else:
        conn.execute(
            "INSERT INTO converter_favorite_tools (user_id, tool_id) VALUES (?,?)",
            (user_id, tool_id)
        )
        conn.commit()
        conn.close()
        return True


# ── Pinned Files ────────────────────────────────────────────────────────────

def pin_file(user_id: int, file_path: str, label: str = "") -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO converter_pinned (user_id, file_path, label) VALUES (?,?,?)",
        (user_id, file_path, label or Path(file_path).name)
    )
    conn.commit()
    conn.close()


def unpin_file(user_id: int, file_path: str) -> None:
    conn = get_connection()
    conn.execute(
        "DELETE FROM converter_pinned WHERE user_id=? AND file_path=?",
        (user_id, file_path)
    )
    conn.commit()
    conn.close()


def get_pinned_files(user_id: int) -> List[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT file_path, label, pinned_at FROM converter_pinned WHERE user_id=? ORDER BY pinned_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Log appender ────────────────────────────────────────────────────────────

def append_log(job_id: str, level: str, message: str) -> None:
    """Append a diagnostic log line (non-blocking intent — fire and forget)."""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO converter_logs (job_id, level, message) VALUES (?,?,?)",
            (job_id, level, message)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # never let logging break conversions
