from memoryos.context import ContextEngine
from memoryos.relationships import RelationshipEngine


print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 09: CONTEXT-AWARE MEMORY")
print("=" * 55)

engine = ContextEngine(
    relationship_engine=RelationshipEngine()
)

cases = [
    (
        "Different projects",
        {
            "content": "MemoryOS uses SQLite.",
            "subject": "MemoryOS",
            "attribute": "database"
        },
        {
            "content": "ReasoningOS uses PostgreSQL.",
            "subject": "ReasoningOS",
            "attribute": "database"
        },
        "different_subject"
    ),
    (
        "Different dates",
        {
            "content": "The project had 10 users in January.",
            "subject": "project",
            "attribute": "user_count",
            "valid_at": "2026-01-01"
        },
        {
            "content": "The project had 100 users in June.",
            "subject": "project",
            "attribute": "user_count",
            "valid_at": "2026-06-01"
        },
        "temporal_change_candidate"
    ),
    (
        "Direct contradiction",
        {
            "content": "MemoryOS uses SQLite.",
            "subject": "MemoryOS",
            "attribute": "database"
        },
        {
            "content": "MemoryOS does not use SQLite.",
            "subject": "MemoryOS",
            "attribute": "database"
        },
        "potential_conflict"
    ),
    (
        "Equivalent facts",
        {
            "content": "Asym develops software using GitHub Codespaces.",
            "subject": "Asym",
            "attribute": "development_environment"
        },
        {
            "content": "Asym writes code using GitHub Codespaces.",
            "subject": "Asym",
            "attribute": "development_environment"
        },
        "equivalent_candidate"
    ),
    (
        "Different attributes",
        {
            "content": "MemoryOS uses SQLite.",
            "subject": "MemoryOS",
            "attribute": "database"
        },
        {
            "content": "MemoryOS is written in Python.",
            "subject": "MemoryOS",
            "attribute": "programming_language"
        },
        "different_attribute"
    ),
    (
        "Same-time numerical conflict",
        {
            "content": "The project has exactly 10 users.",
            "subject": "project",
            "attribute": "user_count",
            "valid_at": "2026-10-12"
        },
        {
            "content": "The project has exactly 100 users.",
            "subject": "project",
            "attribute": "user_count",
            "valid_at": "2026-10-12"
        },
        "potential_conflict"
    )
]

correct = 0

for name, existing, incoming, expected in cases:

    result = engine.compare(existing, incoming)

    actual = result["relationship"]
    passed = actual == expected

    if passed:
        correct += 1

    print(f"\n🔬 TEST: {name}")
    print("Expected:", expected)
    print("Actual:", actual)
    print("Conflict:", result["conflict"])
    print("Reason:", result["reason"])
    print("Result:", "PASS" if passed else "FAIL")

    print("-" * 45)

print("\nFINAL RESULTS")
print(f"Passed: {correct}/{len(cases)}")
print(f"Accuracy: {correct / len(cases) * 100:.1f}%")

print("\nEXPERIMENT 09 COMPLETE")
