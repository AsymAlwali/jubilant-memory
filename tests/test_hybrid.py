from memoryos.hybrid import HybridRelationshipEngine


engine = HybridRelationshipEngine(
    similarity_threshold=0.65
)

experiments = [
    (
        "Equivalent",
        "Asym develops software using GitHub Codespaces.",
        "Asym writes code using GitHub Codespaces.",
        "equivalent_candidate"
    ),
    (
        "Direct contradiction",
        "Asym uses GitHub Codespaces.",
        "Asym does not use GitHub Codespaces.",
        "contradiction"
    ),
    (
        "Unrelated",
        "Asym develops software using GitHub Codespaces.",
        "The Atlantic Ocean contains salt water.",
        "unrelated_candidate"
    ),
    (
        "Additional information",
        "Asym uses Python.",
        "Asym uses Python and JavaScript.",
        "related_or_unrelated"
    ),
    (
        "Project change",
        "MemoryOS uses SQLite for storage.",
        "MemoryOS no longer uses SQLite for storage.",
        "contradiction"
    ),
    (
        "Numerical contradiction",
        "The project has 10 users.",
        "The project has 100 users.",
        "contradiction"
    ),
    (
        "Different projects",
        "MemoryOS uses SQLite.",
        "ReasoningOS uses PostgreSQL.",
        "related_or_unrelated"
    ),
    (
        "Equivalent paraphrase",
        "The application stores information permanently.",
        "The software retains data across restarts.",
        "equivalent_candidate"
    ),
    (
        "Negation",
        "The system supports offline mode.",
        "The system does not support offline mode.",
        "contradiction"
    ),
    (
        "Unrelated technical facts",
        "Python is a programming language.",
        "Saturn has many moons.",
        "unrelated_candidate"
    )
]

print("\nJUBILANT MEMORY")
print("EXPERIMENT 05: HYBRID REASONING")
print("=" * 55)

correct = 0

for name, existing, incoming, expected in experiments:

    result = engine.compare(existing, incoming)

    actual = result["relationship"]

    passed = actual == expected

    if passed:
        correct += 1

    print(f"\nTEST: {name}")
    print("Expected:", expected)
    print("Actual:", actual)
    print("Similarity:", result["similarity"])
    print("NLI used:", result["nli_used"])
    print("Result:", "PASS" if passed else "FAIL")
    print("-" * 45)

print("\nFINAL RESULTS")
print(f"Passed: {correct}/{len(experiments)}")
print(f"Accuracy: {correct / len(experiments) * 100:.1f}%")
print("\nEXPERIMENT COMPLETE")
