import sqlite3
import tempfile
import uuid

from pathlib import Path

from memoryos.grounding import MemoryGroundingEngine


print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 16: GROUNDED EVIDENCE VALIDATION")
print("=" * 65)


with tempfile.TemporaryDirectory() as directory:

    db_path = str(Path(directory) / "grounding.db")

    db = sqlite3.connect(db_path)

    db.execute("""
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            subject TEXT NOT NULL,
            attribute TEXT NOT NULL,
            valid_at TEXT
        )
    """)

    sqlite_id = str(uuid.uuid4())
    mysql_id = str(uuid.uuid4())
    missing_time_id = str(uuid.uuid4())
    unsupported_id = str(uuid.uuid4())

    memories = [
        (
            sqlite_id,
            "MemoryOS uses SQLite.",
            "MemoryOS",
            "database",
            "2026-10-01"
        ),
        (
            mysql_id,
            "MemoryOS uses MySQL.",
            "MemoryOS",
            "database",
            "2026-10-12"
        ),
        (
            missing_time_id,
            "MemoryOS uses PostgreSQL.",
            "MemoryOS",
            "database",
            None
        ),
        (
            unsupported_id,
            "MemoryOS migrated its database.",
            "MemoryOS",
            "database",
            "2026-10-10"
        )
    ]

    db.executemany("""
        INSERT INTO memories
        (
            id, content, subject, attribute, valid_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, memories)

    db.commit()
    db.close()

    engine = MemoryGroundingEngine(db_path)

    print("\n1. TESTING CORRECT OBSERVATION")

    correct = {
        "memory_id": sqlite_id,
        "subject": "MemoryOS",
        "attribute": "database",
        "value": "SQLite",
        "valid_at": "2026-10-01"
    }

    result = engine.validate_claim(sqlite_id, correct)

    assert result["valid"] is True

    print("Correct observation:", result["status"])

    print("\n2. TESTING FABRICATED VALUE")

    fabricated = {
        **correct,
        "value": "PostgreSQL"
    }

    result = engine.validate_claim(sqlite_id, fabricated)

    assert result["valid"] is False
    assert result["field"] == "value"

    print("Fabricated value rejected:", True)

    print("\n3. TESTING FABRICATED TIMESTAMP")

    wrong_time = {
        **correct,
        "valid_at": "2026-10-12"
    }

    result = engine.validate_claim(sqlite_id, wrong_time)

    assert result["valid"] is False
    assert result["field"] == "valid_at"

    print("Fabricated timestamp rejected:", True)

    print("\n4. TESTING WRONG MEMORY REFERENCE")

    wrong_reference = {
        **correct,
        "memory_id": mysql_id
    }

    result = engine.validate_claim(sqlite_id, wrong_reference)

    assert result["valid"] is False
    assert result["field"] == "memory_id"

    print("Wrong memory reference rejected:", True)

    print("\n5. TESTING MISSING TIMESTAMP")

    result = engine.get_grounded_observation(
        missing_time_id
    )

    assert result["status"] == "missing_or_invalid_time"

    print("Missing timestamp:", result["status"])

    print("\n6. TESTING UNSUPPORTED SENTENCE")

    result = engine.get_grounded_observation(
        unsupported_id
    )

    assert result["status"] == "unsupported_format"

    print("Unsupported sentence:", result["status"])

    print("\n7. TESTING NONEXISTENT MEMORY")

    result = engine.get_grounded_observation(
        "nonexistent-memory"
    )

    assert result["status"] == "memory_not_found"

    print("Nonexistent memory:", result["status"])

    print("\n8. VERIFYING DATABASE PERSISTENCE")

    engine.close()

    engine = MemoryGroundingEngine(db_path)

    restored = engine.get_grounded_observation(
        sqlite_id
    )

    assert restored["status"] == "grounded"
    assert restored["observation"]["value"] == "SQLite"

    print("Persisted observation:", restored["status"])

    engine.close()


print("\n" + "=" * 65)
print("✅ EXPERIMENT 16 COMPLETE — ALL ASSERTIONS PASSED")
