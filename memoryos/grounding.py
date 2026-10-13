import re
import sqlite3

from datetime import datetime, timezone


class MemoryGroundingEngine:
    """
    Ground structured observations in persisted memories.

    This prototype supports controlled sentence formats,
    not arbitrary natural language.
    """

    PATTERN = re.compile(
        r"^(?P<subject>[A-Za-z0-9_-]+) uses "
        r"(?P<value>[A-Za-z0-9_.+-]+)\.$"
    )

    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)

    @staticmethod
    def normalize_time(value):
        if not isinstance(value, str) or not value.strip():
            return None

        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc).isoformat()

    def get_grounded_observation(self, memory_id):

        row = self.db.execute("""
            SELECT
                id,
                content,
                subject,
                attribute,
                valid_at
            FROM memories
            WHERE id = ?
        """, (memory_id,)).fetchone()

        if row is None:
            return {
                "status": "memory_not_found",
                "observation": None
            }

        (
            stored_id,
            content,
            subject,
            attribute,
            valid_at
        ) = row

        match = self.PATTERN.fullmatch(content.strip())

        if match is None:
            return {
                "status": "unsupported_format",
                "observation": None
            }

        extracted_subject = match.group("subject")
        extracted_value = match.group("value")

        if extracted_subject != subject:
            return {
                "status": "subject_mismatch",
                "observation": None
            }

        normalized_time = self.normalize_time(valid_at)

        if normalized_time is None:
            return {
                "status": "missing_or_invalid_time",
                "observation": None
            }

        return {
            "status": "grounded",
            "observation": {
                "memory_id": stored_id,
                "subject": subject,
                "attribute": attribute,
                "value": extracted_value,
                "valid_at": normalized_time
            }
        }

    def validate_claim(self, memory_id, claimed_observation):

        grounded = self.get_grounded_observation(memory_id)

        if grounded["status"] != "grounded":
            return {
                "valid": False,
                "status": grounded["status"]
            }

        actual = grounded["observation"]

        if not isinstance(claimed_observation, dict):
            return {
                "valid": False,
                "status": "invalid_claim"
            }

        required_fields = (
            "memory_id",
            "subject",
            "attribute",
            "value",
            "valid_at"
        )

        for field in required_fields:
            if field not in claimed_observation:
                return {
                    "valid": False,
                    "status": "missing_field",
                    "field": field
                }

        claimed_time = self.normalize_time(
            claimed_observation["valid_at"]
        )

        for field in (
            "memory_id",
            "subject",
            "attribute",
            "value"
        ):
            if claimed_observation[field] != actual[field]:
                return {
                    "valid": False,
                    "status": "claim_mismatch",
                    "field": field,
                    "expected": actual[field],
                    "received": claimed_observation[field]
                }

        if claimed_time != actual["valid_at"]:
            return {
                "valid": False,
                "status": "claim_mismatch",
                "field": "valid_at",
                "expected": actual["valid_at"],
                "received": claimed_time
            }

        return {
            "valid": True,
            "status": "grounded",
            "observation": actual
        }

    def close(self):
        self.db.close()
