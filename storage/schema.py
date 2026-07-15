"""Database schema and initialization for TeamAgent."""

import sqlite3
from pathlib import Path
from typing import Optional
import os


def get_database_path(custom_path: Optional[str] = None) -> Path:
    """Get the path to the TeamAgent database.

    Args:
        custom_path: Optional custom database path

    Returns:
        Path to the database file
    """
    if custom_path:
        return Path(custom_path)

    # Default to data/ directory in TeamAgent root
    teamagent_root = Path(__file__).parent.parent
    data_dir = teamagent_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir / "teamagent.db"


def init_database(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Initialize the TeamAgent database with all required tables.

    Args:
        db_path: Optional custom database path

    Returns:
        SQLite connection object
    """
    path = get_database_path(db_path)

    # Enable WAL mode for concurrent access
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Create schema version table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create engineers table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS engineers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            git_username TEXT,
            timezone TEXT DEFAULT 'UTC',
            preferences_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create teams table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            codebase_path TEXT,
            memory_bank_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT,
            FOREIGN KEY (created_by) REFERENCES engineers(id)
        )
    """)

    # Create team_members table (many-to-many relationship)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS team_members (
            team_id TEXT NOT NULL,
            engineer_id TEXT NOT NULL,
            role TEXT DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (team_id, engineer_id),
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
            FOREIGN KEY (engineer_id) REFERENCES engineers(id) ON DELETE CASCADE
        )
    """)

    # Create qa_entries table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS qa_entries (
            id TEXT PRIMARY KEY,
            team_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT,
            asked_by TEXT NOT NULL,
            answered_by TEXT,
            asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            answered_at TIMESTAMP,
            tags TEXT DEFAULT '[]',
            context_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'open',
            upvotes INTEGER DEFAULT 0,
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
            FOREIGN KEY (asked_by) REFERENCES engineers(id),
            FOREIGN KEY (answered_by) REFERENCES engineers(id)
        )
    """)

    # Create FTS5 index for Q&A search (standalone, not content-linked)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS qa_fts USING fts5(
            qa_id UNINDEXED,
            question,
            answer,
            tags
        )
    """)

    # Create triggers to keep FTS5 in sync
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS qa_fts_insert AFTER INSERT ON qa_entries BEGIN
            INSERT INTO qa_fts(qa_id, question, answer, tags)
            VALUES (new.id, new.question, new.answer, new.tags);
        END
    """)

    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS qa_fts_update AFTER UPDATE ON qa_entries BEGIN
            DELETE FROM qa_fts WHERE qa_id = old.id;
            INSERT INTO qa_fts(qa_id, question, answer, tags)
            VALUES (new.id, new.question, new.answer, new.tags);
        END
    """)

    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS qa_fts_delete AFTER DELETE ON qa_entries BEGIN
            DELETE FROM qa_fts WHERE qa_id = old.id;
        END
    """)

    # Create engineer_sessions table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS engineer_sessions (
            id TEXT PRIMARY KEY,
            engineer_id TEXT NOT NULL,
            team_id TEXT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            work_summary TEXT,
            handoff_to TEXT,
            FOREIGN KEY (engineer_id) REFERENCES engineers(id),
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
            FOREIGN KEY (handoff_to) REFERENCES engineers(id)
        )
    """)

    # Create contributions table for attribution metrics
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engineer_id TEXT NOT NULL,
            team_id TEXT NOT NULL,
            contribution_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (engineer_id) REFERENCES engineers(id),
            FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
        )
    """)

    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qa_team ON qa_entries(team_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qa_status ON qa_entries(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_qa_asked_by ON qa_entries(asked_by)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_engineer ON engineer_sessions(engineer_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_team ON engineer_sessions(team_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_contributions_engineer ON contributions(engineer_id)")

    # Record schema version
    current_version = 1
    cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()

    if not row or row[0] < current_version:
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (current_version,))

    conn.commit()
    return conn


if __name__ == "__main__":
    # Initialize database when run directly
    db_path = get_database_path()
    print(f"Initializing TeamAgent database at: {db_path}")
    conn = init_database()
    print(f"Database initialized successfully!")
    conn.close()
