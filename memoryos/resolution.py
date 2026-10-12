import json
import sqlite3
import uuid

from datetime import datetime, timezone

from memoryos.temporal import TemporalEvidenceValidator


class IntegratedResolutionEngine:
    """
    Integrates persistent memory conflicts,
    structured temporal evidence, and review history.

    Uses the same SQLite database as MemoryPipeline.

    This prototype validates evidence consistency,
    not evidence authenticity.
    """

    VALID_DECISIONS = {"explained", "rejected"}

    def __init__(self, db_path):

        self.db = sqlite3.connect(db_path)
        self.db.execute("PRAGMA foreign_keys = ON")

        # Require an existing MemoryPipeline database.
        required_tables = {"memories", "conflicts"}

        existing_tables = {
            row[0]
            for row in self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        if not required_tables.issubset(existing_tables):
            self.db.close()
            raise ValueError(
                "Database must first be initialized by MemoryPipeline"
            )

        self.validator = TemporalEvidenceValidator()

        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS resolution_evidence (
                id TEXT PRIMARY KEY,
                conflict_id TEXT NOT NULL,
                content TEXT NOT NULL,
                event_json TEXT NOT NULL,
                source TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(conflict_id)
                    REFERENCES conflicts(id)
            );

            CREATE TABLE IF NOT EXISTS resolution_reviews (
                id TEXT PRIMARY KEY,
                conflict_id TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                explanation TEXT NOT NULL,
                validation_status TEXT NOT NULL,
                status TEXT NOT NULL,
                reviewer TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(conflict_id)
                    REFERENCES conflicts(id),
                FOREIGN KEY(evidence_id)
                    REFERENCES resolution_evidence(id)
            );

            CREATE TABLE IF NOT EXISTS resolution_history (
                id TEXT PRIMARY KEY,
                review_id TEXT NOT NULL,
                previous_status TEXT,
                new_status TEXT NOT NULL,
                reason TEXT NOT NULL,
                reviewer TEXT,
                changed_at TEXT NOT NULL,
                FOREIGN KEY(review_id)
                    REFERENCES resolution_reviews(id)
            );
        """)

        self.db.commit()

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def get_conflict(self, conflict_id):

        row = self.db.execute("""
            SELECT
                c.id,
                c.existing_id,
                c.incoming_id,
                m1.content,
                m2.content,
                m1.subject,
                m2.subject,
                m1.attribute,
                m2.attribute
            FROM conflicts c
            JOIN memories m1
                ON c.existing_id = m1.id
            JOIN memories m2
                ON c.incoming_id = m2.id
            WHERE c.id = ?
        """, (conflict_id,)).fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "existing_id": row[1],
            "incoming_id": row[2],
            "existing_content": row[3],
            "incoming_content": row[4],
            "existing_subject": row[5],
            "incoming_subject": row[6],
            "existing_attribute": row[7],
            "incoming_attribute": row[8]
        }

    def submit_evidence(
        self,
        conflict_id,
        content,
        event,
        observations,
        source=None
    ):
        """
        Validate structured evidence against observations.

        Creates a resolution candidate only when the
        temporal validator returns explanation_candidate.

        Observations must refer to the actual conflict's
        subject and attribute.

        NOTE: Observation values and dates are supplied
        by the caller in this prototype. Their factual
        correspondence to the stored memory text is
        not automatically verified.
        """

        conflict = self.get_conflict(conflict_id)

        if conflict is None:
            raise ValueError("Conflict does not exist")

        if not isinstance(content, str) or not content.strip():
            raise ValueError("Evidence content is required")

        if not isinstance(event, dict):
            raise ValueError("Event must be a dictionary")

        if not isinstance(observations, list):
            raise ValueError("Observations must be a list")

        if (
            conflict["existing_subject"]
            != conflict["incoming_subject"]
            or conflict["existing_attribute"]
            != conflict["incoming_attribute"]
        ):
            raise ValueError(
                "Conflict memories have incompatible metadata"
            )

        subject = conflict["existing_subject"]
        attribute = conflict["existing_attribute"]

        if (
            event.get("subject") != subject
            or event.get("attribute") != attribute
        ):
            raise ValueError(
                "Evidence event does not match conflict metadata"
            )

        for observation in observations:
            if not isinstance(observation, dict):
                raise ValueError("Each observation must be a dictionary")

            if (
                observation.get("subject") != subject
                or observation.get("attribute") != attribute
            ):
                raise ValueError(
                    "Observation does not match conflict metadata"
                )

        validation = self.validator.evaluate_explanation(
            observations,
            event
        )

        if validation["status"] != "explanation_candidate":
            return {
                "accepted": False,
                "validation": validation,
                "review_id": None,
                "reason": "Evidence did not pass temporal validation."
            }

        evidence_id = str(uuid.uuid4())
        review_id = str(uuid.uuid4())
        now = self._now()

        explanation = (
            f"Proposed transition for {subject}.{attribute}: "
            f"{event['old_value']} -> {event['new_value']} "
            f"at {event['effective_at']}."
        )

        with self.db:

            self.db.execute("""
                INSERT INTO resolution_evidence
                (
                    id, conflict_id, content,
                    event_json, source, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                evidence_id,
                conflict_id,
                content,
                json.dumps({
                    "event": event,
                    "observations": observations
                }),
                source,
                now
            ))

            self.db.execute("""
                INSERT INTO resolution_reviews
                (
                    id, conflict_id, evidence_id,
                    explanation, validation_status,
                    status, reviewer,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review_id,
                conflict_id,
                evidence_id,
                explanation,
                validation["status"],
                "needs_review",
                None,
                now,
                now
            ))

            self.db.execute("""
                INSERT INTO resolution_history
                (
                    id, review_id, previous_status,
                    new_status, reason, reviewer, changed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                review_id,
                None,
                "needs_review",
                "Structured evidence passed consistency checks.",
                None,
                now
            ))

        return {
            "accepted": True,
            "validation": validation,
            "evidence_id": evidence_id,
            "review_id": review_id,
            "status": "needs_review",
            "explanation": explanation
        }

    def review_resolution(
        self,
        review_id,
        decision,
        reviewer,
        reason
    ):

        if decision not in self.VALID_DECISIONS:
            raise ValueError("Invalid review decision")

        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("Reviewer is required")

        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("Review reason is required")

        row = self.db.execute("""
            SELECT status
            FROM resolution_reviews
            WHERE id = ?
        """, (review_id,)).fetchone()

        if row is None:
            raise ValueError("Review does not exist")

        previous_status = row[0]

        if previous_status != "needs_review":
            raise ValueError(
                "Only pending reviews can receive a decision"
            )

        now = self._now()

        with self.db:

            self.db.execute("""
                UPDATE resolution_reviews
                SET
                    status = ?,
                    reviewer = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                decision,
                reviewer,
                now,
                review_id
            ))

            self.db.execute("""
                INSERT INTO resolution_history
                (
                    id, review_id, previous_status,
                    new_status, reason, reviewer, changed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                review_id,
                previous_status,
                decision,
                reason,
                reviewer,
                now
            ))

        return self.get_review(review_id)

    def get_review(self, review_id):

        row = self.db.execute("""
            SELECT
                id, conflict_id, evidence_id,
                explanation, validation_status,
                status, reviewer
            FROM resolution_reviews
            WHERE id = ?
        """, (review_id,)).fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "conflict_id": row[1],
            "evidence_id": row[2],
            "explanation": row[3],
            "validation_status": row[4],
            "status": row[5],
            "reviewer": row[6]
        }

    def get_history(self, review_id):

        rows = self.db.execute("""
            SELECT
                previous_status,
                new_status,
                reason,
                reviewer,
                changed_at
            FROM resolution_history
            WHERE review_id = ?
            ORDER BY rowid
        """, (review_id,)).fetchall()

        return [
            {
                "previous_status": row[0],
                "new_status": row[1],
                "reason": row[2],
                "reviewer": row[3],
                "changed_at": row[4]
            }
            for row in rows
        ]

    def close(self):
        self.db.close()
