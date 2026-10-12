import tempfile
from pathlib import Path

from memoryos.pipeline import MemoryPipeline


print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 10: INTEGRATED MEMORY PIPELINE")
print("=" * 55)

with tempfile.TemporaryDirectory() as directory:

    db_path = str(
        Path(directory) / "pipeline.db"
    )

    memory = MemoryPipeline(db_path)

    print("\n1. STORING INITIAL MEMORY")

    first = memory.remember(
        content="MemoryOS uses SQLite for storage.",
        subject="MemoryOS",
        attribute="database",
        source="experiment_10"
    )

    print("Stored:", first["memory_id"])

    print("\n2. STORING CONTRADICTORY MEMORY")

    second = memory.remember(
        content="MemoryOS does not use SQLite for storage.",
        subject="MemoryOS",
        attribute="database",
        source="experiment_10"
    )

    print("Conflicts:", second["conflicts_detected"])

    assert second["conflicts_detected"] >= 1

    print("\n3. STORING DIFFERENT PROJECT")

    third = memory.remember(
        content="ReasoningOS uses PostgreSQL.",
        subject="ReasoningOS",
        attribute="database",
        source="experiment_10"
    )

    print("Conflicts:", third["conflicts_detected"])

    assert third["conflicts_detected"] == 0

    print("\n4. TESTING SEMANTIC RECALL")

    results = memory.recall(
        "What database does MemoryOS use?"
    )

    for result in results:
        print(
            f"[{result['score']:.3f}]",
            result["content"]
        )

    print("\n5. CHECKING CONFLICT REPORTS")

    conflicts = memory.get_conflicts()

    for conflict in conflicts:
        print("Conflict:", conflict[2], "<->", conflict[3])

    assert len(conflicts) >= 1

    memory.close()

    print("\n6. TESTING PERSISTENCE")

    memory = MemoryPipeline(db_path)

    count = memory.db.execute(
        "SELECT COUNT(*) FROM memories"
    ).fetchone()[0]

    saved_conflicts = memory.get_conflicts()

    print("Persisted memories:", count)
    print("Persisted conflicts:", len(saved_conflicts))

    assert count == 3
    assert len(saved_conflicts) >= 1

    memory.close()

print("\n✅ EXPERIMENT 10 COMPLETE")
