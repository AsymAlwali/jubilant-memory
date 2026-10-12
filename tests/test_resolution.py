import tempfile
import uuid

from pathlib import Path

from memoryos.pipeline import MemoryPipeline
from memoryos.resolution import IntegratedResolutionEngine


print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 14: INTEGRATED EVIDENCE RESOLUTION")
print("=" * 65)

with tempfile.TemporaryDirectory() as directory:

    db_path = str(Path(directory) / "memory.db")

    print("\n1. INITIALIZING MEMORY PIPELINE")

    memory = MemoryPipeline(db_path)

    first = memory.remember(
        content="MemoryOS uses SQLite.",
        subject="MemoryOS",
        attribute="database",
        source="historical_record"
    )

    second = memory.remember(
        content="MemoryOS uses PostgreSQL.",
        subject="MemoryOS",
        attribute="database",
        source="recent_record"
    )

    first_id = first["memory_id"]
    second_id = second["memory_id"]

    conflict_id = str(uuid.uuid4())

    # Insert a synthetic potential conflict for this
    # integration test. This avoids depending on NLI output.
    #
    # Do not use this approach in production ingestion.

    memory.db.execute("""
        INSERT INTO conflicts
        (
            id, existing_id, incoming_id,
            relationship, created_at
        )
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (
        conflict_id,
        first_id,
        second_id,
        "potential_conflict"
    ))

    memory.db.commit()
    memory.close()

    print("Memories stored: 2")
    print("Synthetic conflict:", conflict_id)

    print("\n2. INITIALIZING RESOLUTION ENGINE")

    engine = IntegratedResolutionEngine(db_path)

    conflict = engine.get_conflict(conflict_id)

    assert conflict is not None

    print("Conflict found:", conflict["id"])

    print("\n3. SUBMITTING STRUCTURED EVIDENCE")

    event = {
        "subject": "MemoryOS",
        "attribute": "database",
        "old_value": "SQLite",
        "new_value": "PostgreSQL",
        "effective_at": "2026-10-10"
    }

    observations = [
        {
            "subject": "MemoryOS",
            "attribute": "database",
            "value": "SQLite",
            "valid_at": "2026-10-01"
        },
        {
            "subject": "MemoryOS",
            "attribute": "database",
            "value": "PostgreSQL",
            "valid_at": "2026-10-12"
        }
    ]

    result = engine.submit_evidence(
        conflict_id=conflict_id,
        content=(
            "MemoryOS migrated from SQLite "
            "to PostgreSQL on October 10."
        ),
        event=event,
        observations=observations,
        source="project_changelog"
    )

    assert result["accepted"] is True
    assert result["status"] == "needs_review"

    review_id = result["review_id"]

    print("Validation:", result["validation"]["status"])
    print("Review status:", result["status"])

    print("\n4. TESTING INCORRECT EVIDENCE")

    wrong_event = {
        "subject": "MemoryOS",
        "attribute": "database",
        "old_value": "PostgreSQL",
        "new_value": "SQLite",
        "effective_at": "2026-10-10"
    }

    wrong = engine.submit_evidence(
        conflict_id=conflict_id,
        content="Incorrect migration direction.",
        event=wrong_event,
        observations=observations,
        source="unverified_note"
    )

    assert wrong["accepted"] is False
    assert wrong["review_id"] is None

    print("Incorrect evidence rejected:", True)

    print("\n5. SIMULATING EXPLICIT REVIEW")

    reviewed = engine.review_resolution(
        review_id=review_id,
        decision="explained",
        reviewer="experiment_reviewer",
        reason=(
            "Accepted the proposed migration explanation "
            "for this controlled experiment."
        )
    )

    assert reviewed["status"] == "explained"

    print("Final review status:", reviewed["status"])

    print("\n6. CHECKING AUDIT HISTORY")

    history = engine.get_history(review_id)

    assert len(history) == 2

    for entry in history:
        print(
            entry["previous_status"],
            "->",
            entry["new_status"]
        )

    print("\n7. VERIFYING ORIGINAL MEMORIES")

    count = engine.db.execute("""
        SELECT COUNT(*)
        FROM memories
    """).fetchone()[0]

    conflict_count = engine.db.execute("""
        SELECT COUNT(*)
        FROM conflicts
        WHERE id = ?
    """, (conflict_id,)).fetchone()[0]

    assert count == 2
    assert conflict_count == 1

    print("Original memories:", count)
    print("Original conflict preserved:", bool(conflict_count))

    engine.close()

    print("\n8. TESTING PERSISTENCE")

    engine = IntegratedResolutionEngine(db_path)

    restored = engine.get_review(review_id)
    restored_history = engine.get_history(review_id)

    assert restored["status"] == "explained"
    assert len(restored_history) == 2

    print("Persisted review status:", restored["status"])
    print("Persisted history entries:", len(restored_history))

    engine.close()

print("\n" + "=" * 65)
print("✅ EXPERIMENT 14 COMPLETE — ALL ASSERTIONS PASSED")
