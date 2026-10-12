import tempfile
import uuid

from pathlib import Path

from memoryos.pipeline import MemoryPipeline
from memoryos.resolution import IntegratedResolutionEngine
from memoryos.resolution_recall import ResolutionAwareRecall


print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 15: RESOLUTION-AWARE RECALL")
print("=" * 65)


def create_conflict(db, first_id, second_id):
    conflict_id = str(uuid.uuid4())

    db.execute("""
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

    db.commit()

    return conflict_id


with tempfile.TemporaryDirectory() as directory:

    db_path = str(Path(directory) / "memory.db")

    print("\n1. CREATING MEMORIES")

    pipeline = MemoryPipeline(db_path)

    sqlite_id = pipeline.remember(
        content="MemoryOS uses SQLite.",
        subject="MemoryOS",
        attribute="database"
    )["memory_id"]

    postgres_id = pipeline.remember(
        content="MemoryOS uses PostgreSQL.",
        subject="MemoryOS",
        attribute="database"
    )["memory_id"]

    mysql_id = pipeline.remember(
        content="MemoryOS uses MySQL.",
        subject="MemoryOS",
        attribute="database"
    )["memory_id"]

    unrelated_id = pipeline.remember(
        content="ReasoningOS uses Python.",
        subject="ReasoningOS",
        attribute="language"
    )["memory_id"]

    # Remove automatically detected conflicts in this temporary test database.
    # Experiment 15 tests resolution-aware recall, not NLI detection.
    pipeline.db.execute("DELETE FROM conflicts")
    pipeline.db.commit()

    # Create controlled conflict records so this test
    # does not depend on NLI classification.

    explained_conflict = create_conflict(
        pipeline.db,
        sqlite_id,
        postgres_id
    )

    unresolved_conflict = create_conflict(
        pipeline.db,
        postgres_id,
        mysql_id
    )

    pipeline.close()

    print("Memories created: 4")
    print("Controlled conflicts created: 2")

    print("\n2. ACCEPTING ONE RESOLUTION")

    engine = IntegratedResolutionEngine(db_path)

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

    proposal = engine.submit_evidence(
        conflict_id=explained_conflict,
        content="MemoryOS migrated to PostgreSQL.",
        event=event,
        observations=observations,
        source="project_changelog"
    )

    assert proposal["accepted"] is True

    engine.review_resolution(
        review_id=proposal["review_id"],
        decision="explained",
        reviewer="experiment_reviewer",
        reason="Accepted controlled migration explanation."
    )

    print("First conflict: explained")
    print("Second conflict: unresolved")

    print("\n3. TESTING RESOLUTION-AWARE RECALL")

    recall = ResolutionAwareRecall(db_path)

    results = recall.recall_with_resolutions(
        "What database does MemoryOS use?",
        limit=10
    )

    by_id = {
        result["id"]: result
        for result in results
    }

    assert len(by_id) == 4

    print("DIAGNOSTICS:", [(x["content"], x["status"], [(c["other_memory_content"], c["status"]) for c in x["conflicts"]]) for x in results])
    assert by_id[sqlite_id]["status"] == "explained"

    assert by_id[postgres_id]["status"] == "disputed"

    assert by_id[mysql_id]["status"] == "disputed"

    assert (
        by_id[unrelated_id]["status"]
        == "no_recorded_conflict"
    )

    print("\nRETRIEVED MEMORIES:")

    for item in results:
        print(
            f"- {item['content']} "
            f"| status={item['status']} "
            f"| conflicts={item['conflict_count']}"
        )

    print("\n4. CHECKING ACCEPTED EXPLANATION")

    sqlite_conflicts = by_id[sqlite_id]["conflicts"]

    assert len(sqlite_conflicts) == 1

    accepted = sqlite_conflicts[0]["accepted_explanations"]

    assert len(accepted) == 1

    assert accepted[0]["status"] == "explained"

    print("Accepted explanation:", accepted[0]["explanation"])
    print("Evidence source:", accepted[0]["evidence_source"])

    print("\n5. VERIFYING MULTIPLE-CONFLICT SAFETY")

    postgres_conflicts = by_id[postgres_id]["conflicts"]

    assert len(postgres_conflicts) == 2

    assert {
        conflict["status"]
        for conflict in postgres_conflicts
    } == {"explained", "disputed"}

    assert by_id[postgres_id]["status"] == "disputed"

    print("PostgreSQL memory remains disputed:", True)

    print("\n6. VERIFYING ORIGINAL RECORDS")

    original_memories = recall.resolution.db.execute("""
        SELECT COUNT(*) FROM memories
    """).fetchone()[0]

    original_conflicts = recall.resolution.db.execute("""
        SELECT COUNT(*) FROM conflicts
    """).fetchone()[0]

    assert original_memories == 4
    assert original_conflicts == 2

    print("Original memories:", original_memories)
    print("Original conflicts:", original_conflicts)

    recall.close()
    engine.close()

    print("\n7. RESTARTING THE SYSTEM")

    recall = ResolutionAwareRecall(db_path)

    restored = recall.recall_with_resolutions(
        "What database does MemoryOS use?",
        limit=10
    )

    restored_by_id = {
        item["id"]: item
        for item in restored
    }

    assert restored_by_id[sqlite_id]["status"] == "explained"
    assert restored_by_id[postgres_id]["status"] == "disputed"
    assert restored_by_id[mysql_id]["status"] == "disputed"

    print(
        "Persisted SQLite status:",
        restored_by_id[sqlite_id]["status"]
    )

    print(
        "Persisted PostgreSQL status:",
        restored_by_id[postgres_id]["status"]
    )

    recall.close()

print("\n" + "=" * 65)
print("✅ EXPERIMENT 15 COMPLETE — ALL ASSERTIONS PASSED")
