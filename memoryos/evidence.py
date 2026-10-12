import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


class EvidenceEngine:
    """
    Persistent evidence and conflict-review tracking.

    Evidence is recorded, not automatically trusted.
    """

    VALID_STATUSES = {
        "unresolved",
        "needs_review",
        "explained",
        "rejected",
    }

    def __init__(self, db_path="data/evidence.db"):

        Path(db_path).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.db = sqlite3.connect(db_path)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY,
                conflict_id TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT,
                observed_at TEXT,
                created_at TEXT NOT NULL
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS conflict_reviews (
                id TEXT PRIMARY KEY,
                conflict_id TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                explanation TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS review_history (
                id TEXT PRIMARY KEY,
                review_id TEXT NOT NULL,
                previous_status TEXT,
                new_status TEXT NOT NULL,
                reason TEXT NOT NULL,
                changed_at TEXT NOT NULL
            )
        """)

        self.db.commit()

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def add_evidence(
        self,
        conflict_id,
        content,
        source=None,
        observed_at=None
    ):

        if not conflict_id or not content.strip():
            raise ValueError(
                "Conflict ID and evidence content are required"
            )

        evidence_id = str(uuid.uuid4())

        with self.db:
            self.db.execute("""
                INSERT INTO evidence
                (
                    id, conflict_id, content,
                    source, observed_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                evidence_id,
                conflict_id,
                content,
                source,
                observed_at,
                self._now()
            ))

        return evidence_id

    def propose_resolution(
        self,
        conflict_id,
        evidence_id,
        explanation
    ):

        row = self.db.execute("""
            SELECT conflict_id
            FROM evidence
            WHERE id = ?
        """, (evidence_id,)).fetchone()

        if row is None:
            raise ValueError("Evidence does not exist")

        if row[0] != conflict_id:
            raise ValueError(
                "Evidence belongs to a different conflict"
            )

        if not explanation.strip():
            raise ValueError("Explanation cannot be empty")

        review_id = str(uuid.uuid4())
        now = self._now()

        with self.db:

            self.db.execute("""
                INSERT INTO conflict_reviews
                (
                    id, conflict_id, evidence_id,
                    explanation, status,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                review_id,
                conflict_id,
                evidence_id,
                explanation,
                "needs_review",
                now,
                now
            ))

            self.db.execute("""
                INSERT INTO review_history
                (
                    id, review_id, previous_status,
                    new_status, reason, changed_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                review_id,
                None,
                "needs_review",
                "Resolution proposed",
                now
            ))

        return review_id

    def update_review(
        self,
        review_id,
        status,
        reason
    ):

        if status not in self.VALID_STATUSES:
            raise ValueError("Invalid review status")

        if not reason.strip():
            raise ValueError("A review reason is required")

        row = self.db.execute("""
            SELECT status
            FROM conflict_reviews
            WHERE id = ?
        """, (review_id,)).fetchone()

        if row is None:
            raise ValueError("Review does not exist")

        previous_status = row[0]
        now = self._now()

        with self.db:

            self.db.execute("""
                UPDATE conflict_reviews
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (
                status,
                now,
                review_id
            ))

            self.db.execute("""
                INSERT INTO review_history
                (
                    id, review_id, previous_status,
                    new_status, reason, changed_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                review_id,
                previous_status,
                status,
                reason,
                now
            ))

    def get_review(self, review_id):

        row = self.db.execute("""
            SELECT
                id, conflict_id, evidence_id,
                explanation, status
            FROM conflict_reviews
            WHERE id = ?
        """, (review_id,)).fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "conflict_id": row[1],
            "evidence_id": row[2],
            "explanation": row[3],
            "status": row[4]
        }

    def get_history(self, review_id):

        return self.db.execute("""
            SELECT
                previous_status,
                new_status,
                reason,
                changed_at
            FROM review_history
            WHERE review_id = ?
            ORDER BY rowid
        """, (review_id,)).fetchall()

    def close(self):
        self.db.close()
