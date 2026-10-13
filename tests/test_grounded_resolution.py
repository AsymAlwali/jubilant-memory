import tempfile
import uuid

from pathlib import Path

from memoryos.pipeline import MemoryPipeline
from memoryos.grounded_resolution import GroundedResolutionEngine


print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 17: GROUNDED RESOLUTION")
print("=" * 65)


def create_conflict(db, first_id, second_id):
    conflict_id = str(uuid.uuid4())

    db.execute("""
        INSERT INTO conflicts
        (
            id,
            existing_id,
            incoming_id,
            relationship,
            created_at
        )
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (
        conflict_id,
        first_id,
        second_id,
        "potential_conflict"
    ))

    db.commit()

    return conflict_id


with tempfile.TemporaryDirectory() as directory:

    db_path = str(Path(directory) / "grounded_resolution.db")

    print("\n1. CREATING TIMESTAMPED MEMORIES")

    pipeline = MemoryPipeline(db_path)

    sqlite_id = pipeline.remember(
        content="MemoryOS uses SQLite.",
        subject="MemoryOS",
        attribute="database",
        source="historical_record",
        valid_at="2026-10-01"
    )["memory_id"]

    postgres_id = pipeline.remember(
        content="MemoryOS uses PostgreSQL.",
        subject="MemoryOS",
        attribute="database",
        source="recent_record",
        valid_at="2026-10-12"
    )["memory_id"]

    missing_time_id = pipeline.remember(
        content="MemoryOS uses MySQL.",
        subject="MemoryOS",
        attribute="database",
        source="undated_record"
    )["memory_id"]

    # Isolate this experiment from automatic NLI conflicts.
    # Only the temporary test database is modified.

    pipeline.db.execute("DELETE FROM conflicts")
    pipeline.db.commit()

    valid_conflict = create_conflict(
        pipeline.db,
        sqlite_id,
        postgres_id
    )

    undated_conflict = create_conflict(
        pipeline.db,
        sqlite_id,
        missing_time_id
    )

    pipeline.close()

    print("Memories stored: 3")
    print("Controlled conflicts: 2")

    print("\n2. INITIALIZING GROUNDED RESOLUTION")

    engine = GroundedResolutionEngine(db_path)

    event = {
        "subject": "MemoryOS",
        "attribute": "database",
        "old_value": "SQLite",
        "new_value": "PostgreSQL",
        "effective_at": "2026-10-10"
    }

    print("\n3. SUBMITTING GROUNDED EVIDENCE")

    result = engine.submit_grounded_evidence(
        conflict_id=valid_conflict,
        content=(
            "MemoryOS migrated from SQLite "
            "to PostgreSQL on October 10."
        ),
        event=event,
        source="project_changelog"
    )

    assert result["accepted"] is True
    assert result["status"] == "needs_review"
    assert result["grounding_status"] == "grounded"

    review_id = result["review_id"]

    print("Grounding:", result["grounding_status"])
    print("Validation:", result["validation"]["status"])
    print("Review status:", result["status"])

    print("\n4. TESTING INCORRECT TRANSITION")

    wrong_event = {
        "subject": "MemoryOS",
        "attribute": "database",
        "old_value": "PostgreSQL",
        "new_value": "SQLite",
        "effective_at": "2026-10-10"
    }

    wrong = engine.submit_grounded_evidence(
        conflict_id=valid_conflict,
        content="Incorrect migration direction.",
        event=wrong_event,
        source="unverified_note"
    )

    assert wrong["accepted"] is False
    assert wrong["review_id"] is None
    assert wrong["validation"]["status"] == "inconsistent"

    print("Incorrect transition rejected:", True)

    print("\n5. TESTING MISSING TIMESTAMP")

    undated = engine.submit_grounded_evidence(
        conflict_id=undated_conflict,
        content="Claimed migration involving an undated memory.",
        event=event,
        source="unverified_note"
    )

    assert undated["accepted"] is False
    assert undated["status"] == "grounding_failed"
    assert (
        undated["grounding_status"]
        == "missing_or_invalid_time"
    )

    print("Undated memory rejected:", True)

    print("\n6. TESTING EXPLICIT REVIEW")

    reviewed = engine.review_resolution(
        review_id=review_id,
        decision="explained",
        reviewer="experiment_reviewer",
        reason="Accepted grounded migration explanation."
    )

    assert reviewed["status"] == "explained"

    history = engine.get_history(review_id)

    assert len(history) == 2

    print("Final status:", reviewed["status"])
    print("Audit history entries:", len(history))

    print("\n7. VERIFYING ORIGINAL RECORDS")

    memory_count = engine.db.execute("""
        SELECT COUNT(*) FROM memories
    """).fetchone()[0]

    conflict_count = engine.db.execute("""
        SELECT COUNT(*) FROM conflicts
    """).fetchone()[0]

    assert memory_count == 3
    assert conflict_count == 2

    print("Original memories:", memory_count)
    print("Original conflicts:", conflict_count)

    engine.close()

    print("\n8. TESTING PERSISTENCE")

    engine = GroundedResolutionEngine(db_path)

    restored = engine.get_review(review_id)
    restored_history = engine.get_history(review_id)

    assert restored["status"] == "explained"
    assert len(restored_history) == 2

    print("Persisted review status:", restored["status"])
    print("Persisted history entries:", len(restored_history))

    engine.close()


print("\n" + "=" * 65)
print("✅ EXPERIMENT 17 COMPLETE — ALL ASSERTIONS PASSED")
