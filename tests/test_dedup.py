import tempfile
from pathlib import Path

from memoryos.core import MemoryOS


with tempfile.TemporaryDirectory() as directory:
    db_path = str(Path(directory) / "test.db")

    memory = MemoryOS(db_path=db_path)

    print("\n🧠 JUBILANT MEMORY")
    print("EXPERIMENT 02: DEDUPLICATION")
    print("=" * 45)

    first = memory.remember(
        "Asym develops software using GitHub Codespaces."
    )

    second = memory.remember(
        "Asym develops software using GitHub Codespaces."
    )

    assert first == second
    print("✅ Exact duplicate rejected")

    third = memory.remember(
        "Asym writes code using GitHub Codespaces."
    )

    print("Semantic duplicate detected:", first == third)

    results = memory.recall(
        "Where does Asym develop software?"
    )

    print("\nRetrieved memories:")

    for result in results:
        print(
            f"[{result['score']:.3f}]",
            result["content"]
        )

    count = memory.db.execute(
        "SELECT COUNT(*) FROM memories"
    ).fetchone()[0]

    print("\nTotal stored memories:", count)

    assert count in (1, 2)

    memory.close()

print("\n✅ EXPERIMENT COMPLETE")
