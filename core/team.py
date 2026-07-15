"""Team management and coordination."""

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from pathlib import Path
import os


@dataclass
class Team:
    """Represents a team working on a codebase."""

    id: str
    name: str
    description: Optional[str] = None
    codebase_path: Optional[str] = None
    memory_bank_name: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Team":
        """Create Team from database row."""
        return cls(
            id=row[0],
            name=row[1],
            description=row[2],
            codebase_path=row[3],
            memory_bank_name=row[4],
            created_at=datetime.fromisoformat(row[5]) if row[5] else None,
            created_by=row[6],
        )

    def save(self, conn: sqlite3.Connection):
        """Save or update team in database."""
        conn.execute(
            """
            INSERT INTO teams (id, name, description, codebase_path, memory_bank_name, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                codebase_path=excluded.codebase_path,
                memory_bank_name=excluded.memory_bank_name
            """,
            (
                self.id,
                self.name,
                self.description,
                self.codebase_path,
                self.memory_bank_name,
                self.created_by,
            ),
        )
        conn.commit()

    def add_member(
        self,
        conn: sqlite3.Connection,
        engineer_id: str,
        role: str = "member"
    ):
        """Add an engineer to the team."""
        conn.execute(
            """
            INSERT INTO team_members (team_id, engineer_id, role)
            VALUES (?, ?, ?)
            ON CONFLICT(team_id, engineer_id) DO UPDATE SET role=excluded.role
            """,
            (self.id, engineer_id, role),
        )
        conn.commit()

    def remove_member(self, conn: sqlite3.Connection, engineer_id: str):
        """Remove an engineer from the team."""
        conn.execute(
            "DELETE FROM team_members WHERE team_id = ? AND engineer_id = ?",
            (self.id, engineer_id),
        )
        conn.commit()

    def list_members(self, conn: sqlite3.Connection) -> List[dict]:
        """List all team members with their roles."""
        cursor = conn.execute(
            """
            SELECT e.id, e.name, e.email, tm.role, tm.joined_at
            FROM team_members tm
            JOIN engineers e ON tm.engineer_id = e.id
            WHERE tm.team_id = ?
            ORDER BY tm.joined_at
            """,
            (self.id,),
        )
        return [
            {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "role": row[3],
                "joined_at": row[4],
            }
            for row in cursor.fetchall()
        ]

    def is_member(self, conn: sqlite3.Connection, engineer_id: str) -> bool:
        """Check if an engineer is a member of this team."""
        cursor = conn.execute(
            "SELECT 1 FROM team_members WHERE team_id = ? AND engineer_id = ?",
            (self.id, engineer_id),
        )
        return cursor.fetchone() is not None

    @staticmethod
    def get_by_id(conn: sqlite3.Connection, team_id: str) -> Optional["Team"]:
        """Retrieve team by ID."""
        cursor = conn.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
        row = cursor.fetchone()
        return Team.from_row(row) if row else None

    @staticmethod
    def get_by_name(conn: sqlite3.Connection, name: str) -> Optional["Team"]:
        """Retrieve team by name."""
        cursor = conn.execute("SELECT * FROM teams WHERE name = ?", (name,))
        row = cursor.fetchone()
        return Team.from_row(row) if row else None

    @staticmethod
    def list_all(conn: sqlite3.Connection) -> List["Team"]:
        """List all teams."""
        cursor = conn.execute("SELECT * FROM teams ORDER BY name")
        return [Team.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def list_for_engineer(conn: sqlite3.Connection, engineer_id: str) -> List["Team"]:
        """List all teams an engineer belongs to."""
        cursor = conn.execute(
            """
            SELECT t.* FROM teams t
            JOIN team_members tm ON t.id = tm.team_id
            WHERE tm.engineer_id = ?
            ORDER BY t.name
            """,
            (engineer_id,),
        )
        return [Team.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def create_team(
        conn: sqlite3.Connection,
        name: str,
        created_by: str,
        description: Optional[str] = None,
        codebase_path: Optional[str] = None,
    ) -> "Team":
        """Create a new team with Mnemosyne memory bank.

        Args:
            conn: Database connection
            name: Team name
            created_by: Engineer ID who created the team
            description: Optional team description
            codebase_path: Optional path to team's codebase

        Returns:
            Team instance
        """
        team_id = str(uuid.uuid4())

        # Generate memory bank name
        # Format: team-{sanitized_name}-{short_id}
        sanitized_name = name.lower().replace(" ", "-").replace("_", "-")
        short_id = team_id[:8]
        memory_bank_name = f"team-{sanitized_name}-{short_id}"

        team = Team(
            id=team_id,
            name=name,
            description=description,
            codebase_path=codebase_path,
            memory_bank_name=memory_bank_name,
            created_by=created_by,
        )
        team.save(conn)

        # Add creator as team member with 'admin' role
        team.add_member(conn, created_by, role="admin")

        # Create Mnemosyne memory bank (if Mnemosyne is available)
        try:
            from mnemosyne.core.banks import BankManager
            BankManager.create_bank(memory_bank_name)
        except ImportError:
            # Mnemosyne not installed, skip bank creation
            pass

        return team

    def get_memory(self, engineer_id: str):
        """Get team-scoped Mnemosyne memory instance for an engineer.

        Args:
            engineer_id: Engineer ID accessing the memory

        Returns:
            Mnemosyne instance scoped to this team's bank

        Raises:
            ImportError: If Mnemosyne is not installed
        """
        try:
            from mnemosyne import Mnemosyne
        except ImportError:
            raise ImportError(
                "Mnemosyne is not installed. Install with: pip install mnemosyne-memory"
            )

        if not self.memory_bank_name:
            raise ValueError(f"Team {self.name} does not have a memory bank")

        # Create team-scoped memory instance with author tracking
        return Mnemosyne(
            bank=self.memory_bank_name,
            author_id=engineer_id,
            author_type="engineer",
            channel_id=self.id,  # Team ID as channel
        )


def get_current_team(conn: sqlite3.Connection, engineer_id: str) -> Optional[Team]:
    """Get the current team based on codebase path or environment.

    Priority:
    1. TEAMAGENT_TEAM_ID environment variable
    2. Team with codebase_path matching current working directory
    3. First team the engineer belongs to

    Args:
        conn: Database connection
        engineer_id: Engineer ID

    Returns:
        Team instance or None
    """
    # Check environment variable
    team_id = os.environ.get("TEAMAGENT_TEAM_ID")
    if team_id:
        team = Team.get_by_id(conn, team_id)
        if team and team.is_member(conn, engineer_id):
            return team

    # Check codebase path
    cwd = os.getcwd()
    cursor = conn.execute(
        """
        SELECT t.* FROM teams t
        JOIN team_members tm ON t.id = tm.team_id
        WHERE tm.engineer_id = ? AND t.codebase_path IS NOT NULL
        """,
        (engineer_id,),
    )
    for row in cursor.fetchall():
        team = Team.from_row(row)
        if team.codebase_path and Path(cwd).is_relative_to(Path(team.codebase_path)):
            return team

    # Return first team
    teams = Team.list_for_engineer(conn, engineer_id)
    return teams[0] if teams else None
