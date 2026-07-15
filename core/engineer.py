"""Engineer identity and profile management."""

import sqlite3
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import os
import json


@dataclass
class Engineer:
    """Represents an engineer's profile."""

    id: str
    name: str
    email: str
    git_username: Optional[str] = None
    timezone: str = "UTC"
    preferences: dict = None
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}

    @classmethod
    def from_row(cls, row: tuple) -> "Engineer":
        """Create Engineer from database row."""
        return cls(
            id=row[0],
            name=row[1],
            email=row[2],
            git_username=row[3],
            timezone=row[4],
            preferences=json.loads(row[5]) if row[5] else {},
            created_at=datetime.fromisoformat(row[6]) if row[6] else None,
            last_active=datetime.fromisoformat(row[7]) if row[7] else None,
        )

    def save(self, conn: sqlite3.Connection):
        """Save or update engineer profile in database."""
        conn.execute(
            """
            INSERT INTO engineers (id, name, email, git_username, timezone, preferences_json, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                email=excluded.email,
                git_username=excluded.git_username,
                timezone=excluded.timezone,
                preferences_json=excluded.preferences_json,
                last_active=excluded.last_active
            """,
            (
                self.id,
                self.name,
                self.email,
                self.git_username,
                self.timezone,
                json.dumps(self.preferences),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, engineer_id: str) -> Optional["Engineer"]:
        """Retrieve engineer by ID."""
        cursor = conn.execute(
            "SELECT * FROM engineers WHERE id = ?", (engineer_id,)
        )
        row = cursor.fetchone()
        return Engineer.from_row(row) if row else None

    @staticmethod
    def get_by_email(conn: sqlite3.Connection, email: str) -> Optional["Engineer"]:
        """Retrieve engineer by email."""
        cursor = conn.execute(
            "SELECT * FROM engineers WHERE email = ?", (email,)
        )
        row = cursor.fetchone()
        return Engineer.from_row(row) if row else None

    @staticmethod
    def list_all(conn: sqlite3.Connection) -> list["Engineer"]:
        """List all engineers."""
        cursor = conn.execute("SELECT * FROM engineers ORDER BY name")
        return [Engineer.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def get_or_create(
        conn: sqlite3.Connection,
        name: str,
        email: str,
        git_username: Optional[str] = None
    ) -> "Engineer":
        """Get existing engineer by email or create new one."""
        # Try to get by email first
        existing = Engineer.get_by_email(conn, email)
        if existing:
            return existing

        # Create new engineer
        engineer = Engineer(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            git_username=git_username,
            timezone="UTC",
            preferences={},
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        engineer.save(conn)
        return engineer


def _get_git_config(key: str) -> Optional[str]:
    """Get a value from git config."""
    try:
        result = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def whoami(conn: sqlite3.Connection, auto_create: bool = True) -> Optional[Engineer]:
    """Auto-detect current engineer from git config or environment.

    Priority:
    1. TEAMAGENT_ENGINEER_ID environment variable
    2. Git config user.email
    3. System user + hostname as fallback

    Args:
        conn: Database connection
        auto_create: If True, create new engineer profile if not found

    Returns:
        Engineer instance or None
    """
    # Check environment variable first
    engineer_id = os.environ.get("TEAMAGENT_ENGINEER_ID")
    if engineer_id:
        engineer = Engineer.get_by_id(conn, engineer_id)
        if engineer:
            return engineer

    # Try git config
    git_name = _get_git_config("user.name")
    git_email = _get_git_config("user.email")

    if git_email:
        # Check if engineer exists with this email
        engineer = Engineer.get_by_email(conn, git_email)
        if engineer:
            # Update last_active
            engineer.last_active = datetime.now()
            engineer.save(conn)
            return engineer

        # Create new engineer if auto_create enabled
        if auto_create and git_name:
            engineer = Engineer(
                id=str(uuid.uuid4()),
                name=git_name,
                email=git_email,
                git_username=git_name,
                timezone=os.environ.get("TZ", "UTC"),
            )
            engineer.save(conn)
            return engineer

    # Fallback to system user
    try:
        import pwd
        user_info = pwd.getpwuid(os.getuid())
        username = user_info.pw_name
        # Try to construct email
        hostname = subprocess.run(
            ["hostname"],
            capture_output=True,
            text=True,
        ).stdout.strip()

        fallback_email = f"{username}@{hostname}"

        engineer = Engineer.get_by_email(conn, fallback_email)
        if engineer:
            return engineer

        if auto_create:
            engineer = Engineer(
                id=str(uuid.uuid4()),
                name=username,
                email=fallback_email,
                git_username=username,
            )
            engineer.save(conn)
            return engineer

    except Exception:
        pass

    return None
