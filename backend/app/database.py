import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from backend.app.config import DB_PATH

def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tasks Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority TEXT DEFAULT 'medium', -- low, medium, high, urgent
                status TEXT DEFAULT 'pending', -- pending, in_progress, completed
                due_date TEXT,
                duration_minutes INTEGER DEFAULT 30,
                category TEXT DEFAULT 'General',
                tags TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)

        # Reminders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                remind_at TEXT NOT NULL,
                recurrence TEXT DEFAULT 'none', -- none, daily, weekly
                status TEXT DEFAULT 'pending', -- pending, dismissed, snoozed
                created_at TEXT NOT NULL
            )
        """)

        # Personal Memory Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL, -- preference, goal, habit, fact, constraint
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Documents Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                page_count INTEGER DEFAULT 1,
                summary TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

        # Document Chunks Table for RAG
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                page_number INTEGER DEFAULT 1,
                content TEXT NOT NULL,
                embedding_json TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
            )
        """)

        # Agent Tool & Workflow Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                action TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                status TEXT DEFAULT 'success', -- success, failed, approval_required
                execution_time_ms INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        # Chat Message History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL, -- user, assistant, system, tool
                content TEXT NOT NULL,
                agent_name TEXT DEFAULT 'NOVA',
                metadata_json TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            )
        """)

        # User Configuration / Settings key-value store
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Seed initial memories and sample tasks if empty
        cursor.execute("SELECT COUNT(*) as count FROM memories")
        if cursor.fetchone()["count"] == 0:
            now = datetime.now().isoformat()
            initial_memories = [
                ("preference", "preferred_language", "Java", 0.95, now, now),
                ("goal", "learning_target", "Machine Learning & Deep Learning", 0.95, now, now),
                ("preference", "preferred_study_time", "6:00 PM", 0.9, now, now),
                ("habit", "daily_schedule_review", "Every morning at 8:00 AM", 0.85, now, now),
                ("preference", "multilingual_choice", "English and Tamil", 0.9, now, now),
            ]
            cursor.executemany("""
                INSERT INTO memories (category, key, value, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, initial_memories)

        cursor.execute("SELECT COUNT(*) as count FROM tasks")
        if cursor.fetchone()["count"] == 0:
            now = datetime.now().isoformat()
            sample_tasks = [
                ("Review Java multithreading & memory model", "Study concurrency package and synchronization patterns", "high", "pending", "2026-10-29T18:00:00", 120, "Study", "java,coding", now, now, None),
                ("Design RAG vector pipeline for NOVA AI", "Implement chunking and cosine similarity embeddings search", "urgent", "in_progress", "2026-10-28T22:30:00", 90, "Development", "ai,architecture", now, now, None),
                ("Prepare machine learning study roadmap", "Collect notes on neural architectures and loss functions", "medium", "completed", "2026-10-27T17:00:00", 60, "Learning", "ml,datascience", now, now, now),
                ("Weekly productivity sprint review", "Analyze completed tasks and optimize reminder timings", "low", "pending", "2026-10-31T10:00:00", 45, "Review", "productivity,planning", now, now, None),
            ]
            cursor.executemany("""
                INSERT INTO tasks (title, description, priority, status, due_date, duration_minutes, category, tags, created_at, updated_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_tasks)

        cursor.execute("SELECT COUNT(*) as count FROM reminders")
        if cursor.fetchone()["count"] == 0:
            now = datetime.now().isoformat()
            sample_reminders = [
                ("Start Java Concurrency Deep Dive", "2026-10-29T18:00:00", "none", "pending", now),
                ("Team Architecture Sync on NOVA AI", "2026-10-30T11:00:00", "daily", "pending", now),
                ("Productivity Journal & Daily Review", "2026-10-28T22:00:00", "daily", "pending", now),
            ]
            cursor.executemany("""
                INSERT INTO reminders (title, remind_at, recurrence, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, sample_reminders)

