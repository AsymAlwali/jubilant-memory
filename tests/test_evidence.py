import tempfile
from pathlib import Path

from memoryos.evidence import EvidenceEngine


print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 12: EVIDENCE-AWARE CONFLICT RESOLUTION")
print("=" * 60)

with tempfile.TemporaryDirectory() as directory:

    db_path = str(Path(directory) / "evidence.db")

    engine = EvidenceEngine(db_path)

    conflict_id = "experiment-conflict-001"

    print("\n1. ADDING NEW EVIDENCE")

    evidence_id = engine.add_evidence(
        conflict_id=conflict_id,
        content=(
            "MemoryOS migrated from SQLite "
            "to PostgreSQL on October 10."
        ),
        source="project_changelog",
        observed_at="2026-10-10"
    )

    print("Evidence stored:", evidence_id)

    print("\n2. PROPOSING AN EXPLANATION")

    review_id = engine.propose_resolution(
        conflict_id=conflict_id,
        evidence_id=evidence_id,
        explanation=(
            "The two database statements may describe "
            "different periods before and after migration."
        )
    )

    review = engine.get_review(review_id)

    print("Review status:", review["status"])

    assert review["status"] == "needs_review"

    print("\n3. CHECKING INITIAL HISTORY")

    history = engine.get_history(review_id)

    assert len(history) == 1
    assert history[0][1] == "needs_review"

    print("History entries:", len(history))

    print("\n4. SIMULATING AN EXPLICIT REVIEW DECISION")

    engine.update_review(
        review_id=review_id,
        status="explained",
        reason=(
            "Reviewer accepted the migration explanation "
            "for this experiment."
        )
    )

    updated = engine.get_review(review_id)

    assert updated["status"] == "explained"

    print("Updated status:", updated["status"])

    print("\n5. CHECKING AUDIT HISTORY")

    history = engine.get_history(review_id)

    for entry in history:
        print(
            f"{entry[0]} -> {entry[1]} | {entry[2]}"
        )

    assert len(history) == 2

    engine.close()

    print("\n6. RESTARTING EVIDENCE ENGINE")

    engine = EvidenceEngine(db_path)

    restored = engine.get_review(review_id)
    restored_history = engine.get_history(review_id)

    assert restored["status"] == "explained"
    assert len(restored_history) == 2

    print("Persisted status:", restored["status"])
    print("Persisted history entries:", len(restored_history))

    engine.close()

print("\n" + "=" * 60)
print("✅ EXPERIMENT 12 COMPLETE — ALL ASSERTIONS PASSED")
