from memoryos.relationships import RelationshipEngine


print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 04: MEMORY RELATIONSHIPS")
print("=" * 45)

engine = RelationshipEngine()

experiments = [
    (
        "EQUIVALENT",
        "Asym develops software using GitHub Codespaces.",
        "Asym writes code using GitHub Codespaces."
    ),
    (
        "CONTRADICTION",
        "Asym develops software using GitHub Codespaces.",
        "Asym does not develop software using GitHub Codespaces."
    ),
    (
        "UNRELATED",
        "Asym develops software using GitHub Codespaces.",
        "The Atlantic Ocean contains salt water."
    ),
    (
        "ADDITIONAL INFORMATION",
        "Asym uses Python.",
        "Asym uses Python and JavaScript."
    ),
    (
        "PROJECT CHANGE",
        "MemoryOS uses SQLite for storage.",
        "MemoryOS no longer uses SQLite for storage."
    )
]

for expected, existing, incoming in experiments:
    result = engine.classify(existing, incoming)

    print(f"\n🔬 TEST: {expected}")

    print("Existing:", existing)
    print("Incoming:", incoming)

    print(
        "Relationship:",
        result["relationship"]
    )

    print(
        "Contradiction:",
        result["contradiction_score"]
    )

    print(
        "Mutual entailment:",
        result["mutual_entailment_score"]
    )

    print("-" * 45)

print("\n✅ EXPERIMENT 04 COMPLETE")
