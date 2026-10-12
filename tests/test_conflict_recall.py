import tempfile
from pathlib import Path

from memoryos.pipeline import MemoryPipeline


print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 11: CONFLICT-AWARE RECALL")
print("=" * 60)

with tempfile.TemporaryDirectory() as directory:

    db_path = str(Path(directory) / "memory.db")

    memory = MemoryPipeline(db_path)

    print("\n1. STORING ORIGINAL MEMORY")

    original = memory.remember(
        content="MemoryOS uses SQLite for storage.",
        subject="MemoryOS",
        attribute="database",
        source="experiment_11"
    )

    print("Stored:", original["memory_id"])

    print("\n2. STORING CONTRADICTORY MEMORY")

    contradiction = memory.remember(
        content="MemoryOS does not use SQLite for storage.",
        subject="MemoryOS",
        attribute="database",
        source="experiment_11"
    )

    assert contradiction["conflicts_detected"] == 1

    print("Conflicts detected:", contradiction["conflicts_detected"])

    print("\n3. STORING UNRELATED MEMORY")

    unrelated = memory.remember(
        content="ReasoningOS uses PostgreSQL.",
        subject="ReasoningOS",
        attribute="database",
        source="experiment_11"
    )

    assert unrelated["conflicts_detected"] == 0

    print("\n4. TESTING CONFLICT-AWARE RECALL")

    results = memory.recall_with_conflicts(
        "What database does MemoryOS use?",
        limit=5
    )

    for result in results:

        print("\nMEMORY:", result["content"])
        print("Similarity:", result["score"])
        print("Status:", result["status"])
        print("Conflict count:", result["conflict_count"])

        for conflict in result["conflicting_memories"]:
            print("  ↳ Conflicts with:", conflict["content"])

    by_id = {
        item["id"]: item
        for item in results
    }

    original_id = original["memory_id"]
    contradiction_id = contradiction["memory_id"]
    unrelated_id = unrelated["memory_id"]

    # Both sides must be marked disputed.
    assert by_id[original_id]["status"] == "disputed"
    assert by_id[contradiction_id]["status"] == "disputed"

    # Each side should point to the other.
    assert (
        by_id[original_id]["conflicting_memories"][0]["memory_id"]
        == contradiction_id
    )

    assert (
        by_id[contradiction_id]["conflicting_memories"][0]["memory_id"]
        == original_id
    )

    # Unrelated memory should have no recorded conflict.
    assert (
        by_id[unrelated_id]["status"]
        == "no_recorded_conflict"
    )

    assert by_id[unrelated_id]["conflict_count"] == 0

    print("\n✅ Conflict-aware recall assertions passed")

    print("\n5. TESTING DATABASE PERSISTENCE")

    memory.close()

    memory = MemoryPipeline(db_path)

    restored = memory.recall_with_conflicts(
        "What database does MemoryOS use?",
        limit=5
    )

    restored_by_id = {
        item["id"]: item
        for item in restored
    }

    assert restored_by_id[original_id]["status"] == "disputed"
    assert restored_by_id[contradiction_id]["status"] == "disputed"

    assert (
        restored_by_id[original_id]["conflict_count"] == 1
    )

    print("Persisted memories:", len(restored))
    print(
        "Persisted disputed memories:",
        sum(
            item["status"] == "disputed"
            for item in restored
        )
    )

    memory.close()

print("\n" + "=" * 60)
print("✅ EXPERIMENT 11 COMPLETE — ALL ASSERTIONS PASSED")
