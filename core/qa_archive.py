"""Q&A archive system for team knowledge."""

import sqlite3
import uuid
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class QAEntry:
    """Represents a question/answer pair."""

    id: str
    team_id: str
    question: str
    answer: Optional[str] = None
    asked_by: str = ""
    answered_by: Optional[str] = None
    asked_at: Optional[datetime] = None
    answered_at: Optional[datetime] = None
    tags: List[str] = None
    context: dict = None
    status: str = "open"
    upvotes: int = 0

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.context is None:
            self.context = {}

    @classmethod
    def from_row(cls, row: tuple) -> "QAEntry":
        """Create QAEntry from database row."""
        return cls(
            id=row[0],
            team_id=row[1],
            question=row[2],
            answer=row[3],
            asked_by=row[4],
            answered_by=row[5],
            asked_at=datetime.fromisoformat(row[6]) if row[6] else None,
            answered_at=datetime.fromisoformat(row[7]) if row[7] else None,
            tags=json.loads(row[8]) if row[8] else [],
            context=json.loads(row[9]) if row[9] else {},
            status=row[10],
            upvotes=row[11],
        )


class QAArchive:
    """Manager for team Q&A archive with search capabilities."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def ask(
        self,
        team_id: str,
        question: str,
        asked_by: str,
        tags: Optional[List[str]] = None,
        context: Optional[dict] = None,
    ) -> QAEntry:
        """Create a new question.

        Args:
            team_id: Team ID
            question: Question text
            asked_by: Engineer ID who asked
            tags: Optional list of tags
            context: Optional context dictionary

        Returns:
            QAEntry instance
        """
        entry_id = str(uuid.uuid4())
        tags = tags or []
        context = context or {}

        self.conn.execute(
            """
            INSERT INTO qa_entries (id, team_id, question, asked_by, tags, context_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (entry_id, team_id, question, asked_by, json.dumps(tags), json.dumps(context)),
        )
        self.conn.commit()

        return self.get_by_id(entry_id)

    def answer(
        self,
        qa_id: str,
        answer: str,
        answered_by: str,
    ) -> Optional[QAEntry]:
        """Answer an existing question.

        Args:
            qa_id: Q&A entry ID
            answer: Answer text
            answered_by: Engineer ID who answered

        Returns:
            Updated QAEntry instance or None if not found
        """
        self.conn.execute(
            """
            UPDATE qa_entries
            SET answer = ?, answered_by = ?, answered_at = ?, status = 'answered'
            WHERE id = ?
            """,
            (answer, answered_by, datetime.now().isoformat(), qa_id),
        )
        self.conn.commit()

        return self.get_by_id(qa_id)

    def search(
        self,
        team_id: str,
        query: str,
        limit: int = 10,
        status: Optional[str] = None,
    ) -> List[QAEntry]:
        """Search Q&A entries using FTS5.

        Args:
            team_id: Team ID to search within
            query: Search query
            limit: Maximum results to return
            status: Optional status filter ('open', 'answered')

        Returns:
            List of matching QAEntry instances
        """
        # Convert query to FTS5 format: tokenize and OR the terms
        # This allows matching any of the search terms rather than exact phrase
        # Remove special FTS5 characters and split into words
        import re
        words = re.findall(r'\w+', query.lower())
        if not words:
            return []  # No valid search terms

        # Create OR query: word1 OR word2 OR word3
        fts_query = ' OR '.join(words)

        # Use FTS5 for full-text search
        # First query FTS5 for matching qa_ids, then join with qa_entries
        sql = """
            SELECT q.*
            FROM qa_fts f
            JOIN qa_entries q ON f.qa_id = q.id
            WHERE q.team_id = ? AND qa_fts MATCH ?
        """
        params = [team_id, fts_query]

        if status:
            sql += " AND q.status = ?"
            params.append(status)

        sql += " ORDER BY f.rank LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(sql, params)
        return [QAEntry.from_row(row) for row in cursor.fetchall()]

    def search_by_tags(
        self,
        team_id: str,
        tags: List[str],
        limit: int = 10,
    ) -> List[QAEntry]:
        """Search Q&A entries by tags.

        Args:
            team_id: Team ID to search within
            tags: List of tags to match
            limit: Maximum results

        Returns:
            List of matching QAEntry instances
        """
        # Build tag query using FTS5
        tag_query = " OR ".join(tags)

        cursor = self.conn.execute(
            """
            SELECT q.*
            FROM qa_entries q
            JOIN qa_fts f ON q.id = f.qa_id
            WHERE q.team_id = ? AND f.tags MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (team_id, tag_query, limit),
        )
        return [QAEntry.from_row(row) for row in cursor.fetchall()]

    def get_by_id(self, qa_id: str) -> Optional[QAEntry]:
        """Get Q&A entry by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM qa_entries WHERE id = ?", (qa_id,)
        )
        row = cursor.fetchone()
        return QAEntry.from_row(row) if row else None

    def list_recent(
        self,
        team_id: str,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[QAEntry]:
        """List recent Q&A entries for a team.

        Args:
            team_id: Team ID
            limit: Maximum results
            status: Optional status filter

        Returns:
            List of QAEntry instances
        """
        sql = "SELECT * FROM qa_entries WHERE team_id = ?"
        params = [team_id]

        if status:
            sql += " AND status = ?"
            params.append(status)

        sql += " ORDER BY asked_at DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(sql, params)
        return [QAEntry.from_row(row) for row in cursor.fetchall()]

    def list_unanswered(
        self,
        team_id: str,
        limit: int = 20,
    ) -> List[QAEntry]:
        """List unanswered questions for a team."""
        return self.list_recent(team_id, limit=limit, status="open")

    def upvote(self, qa_id: str) -> Optional[QAEntry]:
        """Upvote a Q&A entry (marks it as helpful)."""
        self.conn.execute(
            "UPDATE qa_entries SET upvotes = upvotes + 1 WHERE id = ?",
            (qa_id,),
        )
        self.conn.commit()
        return self.get_by_id(qa_id)

    def get_stats(self, team_id: str) -> dict:
        """Get Q&A statistics for a team."""
        cursor = self.conn.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open,
                SUM(CASE WHEN status = 'answered' THEN 1 ELSE 0 END) as answered
            FROM qa_entries
            WHERE team_id = ?
            """,
            (team_id,),
        )
        row = cursor.fetchone()
        return {
            "total": row[0],
            "open": row[1],
            "answered": row[2],
        }

    def get_top_contributors(self, team_id: str, limit: int = 5) -> List[dict]:
        """Get top contributors (by answers provided)."""
        cursor = self.conn.execute(
            """
            SELECT e.id, e.name, COUNT(*) as answer_count
            FROM qa_entries q
            JOIN engineers e ON q.answered_by = e.id
            WHERE q.team_id = ? AND q.status = 'answered'
            GROUP BY e.id, e.name
            ORDER BY answer_count DESC
            LIMIT ?
            """,
            (team_id, limit),
        )
        return [
            {"id": row[0], "name": row[1], "answer_count": row[2]}
            for row in cursor.fetchall()
        ]
