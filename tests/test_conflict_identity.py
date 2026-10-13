import tempfile

from pathlib import Path

from memoryos.pipeline import MemoryPipeline
from memoryos.conflict_identity import ConflictIdentityEngine
from memoryos.resolution import IntegratedResolutionEngine


print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 18: CONFLICT IDENTITY")
print("=" * 65)


with tempfile.TemporaryDirectory() as directory:

    db_path = str(Path(directory) / "conflict_identity.db")

    print("\n1. CREATING MEMORIES")

    pipeline = MemoryPipeline(db_path)

    first_id = pipeline.remember(
        content="MemoryOS uses SQLite.",
        subject="MemoryOS",
        attribute="database",
        valid_at="2026-10-01"
    )["memory_id"]

    second_id = pipeline.remember(
        content="MemoryOS uses PostgreSQL.",
        subject="MemoryOS",
        attribute="database",
        valid_at="2026-10-12"
    )["memory_id"]

    # Isolate the experiment from automatically generated
    # conflicts in this temporary database.
    pipeline.db.execute("DELETE FROM conflicts")
    pipeline.db.commit()
    pipeline.close()

    print("Memories created: 2")

    print("\n2. TESTING CANONICAL IDENTITY")

    forward_pair = ConflictIdentityEngine.canonical_pair(
        first_id,
        second_id
    )

    reverse_pair = ConflictIdentityEngine.canonical_pair(
        second_id,
        first_id
    )

    assert forward_pair == reverse_pair

    print("Forward and reverse identities match:", True)

    print("\n3. CREATING FIRST CONFLICT")

    identity = ConflictIdentityEngine(db_path)

    first = identity.get_or_create(
        first_id,
        second_id
    )

    assert first["created"] is True

    conflict_id = first["conflict_id"]

    print("First conflict created:", True)

    print("\n4. TESTING REPEATED DETECTION")

    repeated = identity.get_or_create(
        first_id,
        second_id
    )

    assert repeated["created"] is False
    assert repeated["conflict_id"] == conflict_id

    print("Repeated detection reused identity:", True)

    print("\n5. TESTING REVERSE DETECTION")

    reversed_result = identity.get_or_create(
        second_id,
        first_id
    )

    assert reversed_result["created"] is False
    assert reversed_result["conflict_id"] == conflict_id

    print("Reverse detection reused identity:", True)

    print("\n6. TESTING INVALID PAIRS")

    try:
        identity.get_or_create(first_id, first_id)
        raise AssertionError("Self-conflict was accepted")
    except ValueError:
        print("Self-conflict rejected:", True)

    try:
        identity.get_or_create(first_id, "missing-memory")
        raise AssertionError("Missing memory was accepted")
    except ValueError:
        print("Missing memory rejected:", True)

    print("\n7. TESTING REVIEW PRESERVATION")

    resolver = IntegratedResolutionEngine(db_path)

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

    evidence = resolver.submit_evidence(
        conflict_id=conflict_id,
        content="MemoryOS migrated databases.",
        event=event,
        observations=observations,
        source="experiment_changelog"
    )

    assert evidence["accepted"] is True

    review_id = evidence["review_id"]

    reviewed = resolver.review_resolution(
        review_id=review_id,
        decision="explained",
        reviewer="experiment_reviewer",
        reason="Accepted transition explanation."
    )

    assert reviewed["status"] == "explained"

    history_before = resolver.get_history(review_id)

    repeated_after_review = identity.get_or_create(
        second_id,
        first_id
    )

    assert repeated_after_review["created"] is False
    assert repeated_after_review["conflict_id"] == conflict_id

    history_after = resolver.get_history(review_id)

    assert history_before == history_after

    print("Accepted review preserved:", True)
    print("Audit history preserved:", True)

    print("\n8. VERIFYING DATABASE COUNTS")

    conflict_count = identity.db.execute("""
        SELECT COUNT(*) FROM conflicts
    """).fetchone()[0]

    identity_count = identity.db.execute("""
        SELECT COUNT(*) FROM conflict_identity
    """).fetchone()[0]

    assert conflict_count == 1
    assert identity_count == 1

    print("Conflict records:", conflict_count)
    print("Identity records:", identity_count)

    resolver.close()
    identity.close()

    print("\n9. TESTING RESTART AND SECOND CONNECTION")

    reopened = ConflictIdentityEngine(db_path)

    restored = reopened.get_or_create(
        second_id,
        first_id
    )

    assert restored["created"] is False
    assert restored["conflict_id"] == conflict_id

    print("Persisted identity reused:", True)

    second_connection = ConflictIdentityEngine(db_path)

    again = second_connection.get_or_create(
        first_id,
        second_id
    )

    assert again["created"] is False
    assert again["conflict_id"] == conflict_id

    print("Second connection reused identity:", True)

    final_count = reopened.db.execute("""
        SELECT COUNT(*) FROM conflicts
    """).fetchone()[0]

    assert final_count == 1

    print("Final conflict count:", final_count)

    second_connection.close()
    reopened.close()


print("\n" + "=" * 65)
print("✅ EXPERIMENT 18 COMPLETE — ALL ASSERTIONS PASSED")
