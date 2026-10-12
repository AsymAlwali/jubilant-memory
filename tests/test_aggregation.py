from memoryos.relationships import RelationshipEngine

print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 08: NLI AGGREGATION")
print("=" * 55)

engine = RelationshipEngine()

# True = contradiction
# False = not a contradiction
#
# Examples assume the same time and context
# unless explicitly stated otherwise.

cases = [
    (
        "Direct negation",
        "Asym uses Python.",
        "Asym does not use Python.",
        True
    ),
    (
        "Unrelated facts",
        "Asym uses Python.",
        "The Atlantic Ocean contains salt water.",
        False
    ),
    (
        "Different projects",
        "MemoryOS uses SQLite.",
        "ReasoningOS uses PostgreSQL.",
        False
    ),
    (
        "Identical statements",
        "Asym uses Python.",
        "Asym uses Python.",
        False
    ),
    (
        "Numerical contradiction",
        "The project has exactly 10 users.",
        "The project has exactly 100 users.",
        True
    ),
    (
        "Partial information",
        "Asym uses Python.",
        "Asym uses Python and JavaScript.",
        False
    ),
    (
        "Project change",
        "MemoryOS currently uses SQLite.",
        "MemoryOS currently does not use SQLite.",
        True
    ),
    (
        "Offline support",
        "The application supports offline mode.",
        "The application does not support offline mode.",
        True
    ),
    (
        "Different subjects",
        "Alice uses Python.",
        "Bob does not use Python.",
        False
    ),
    (
        "Different dates",
        "The project had 10 users in January.",
        "The project had 100 users in June.",
        False
    ),
    (
        "Equivalent wording",
        "Asym develops software.",
        "Asym writes computer programs.",
        False
    ),
    (
        "Opposite locations",
        "The server is located in Nigeria.",
        "The server is not located in Nigeria.",
        True
    )
]

threshold = 0.80

strategies = {
    "maximum": lambda a, b: max(a, b),
    "minimum": lambda a, b: min(a, b),
    "average": lambda a, b: (a + b) / 2
}

metrics = {
    name: {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    for name in strategies
}

print("\nRunning NLI predictions...\n")

for name, first, second, expected in cases:

    # Use the existing model in both directions
    forward = engine._predict(first, second)
    backward = engine._predict(second, first)

    a = forward["contradiction"]
    b = backward["contradiction"]

    print(f"\nTEST: {name}")
    print(f"Forward contradiction:  {a:.4f}")
    print(f"Backward contradiction: {b:.4f}")
    print(f"Expected contradiction: {expected}")

    for strategy, calculate in strategies.items():

        score = calculate(a, b)
        predicted = score >= threshold

        if predicted and expected:
            outcome = "TP"
        elif predicted and not expected:
            outcome = "FP"
        elif not predicted and expected:
            outcome = "FN"
        else:
            outcome = "TN"

        metrics[strategy][outcome] += 1

        print(
            f"  {strategy:<8} "
            f"score={score:.4f} "
            f"prediction={predicted} "
            f"outcome={outcome}"
        )

print("\n" + "=" * 65)
print("FINAL BENCHMARK RESULTS")
print("=" * 65)

print(
    f"{'Strategy':<10}"
    f"{'TP':<5}"
    f"{'FP':<5}"
    f"{'TN':<5}"
    f"{'FN':<5}"
    f"{'Precision':<12}"
    f"{'Recall':<10}"
)

for strategy, result in metrics.items():

    tp = result["TP"]
    fp = result["FP"]
    tn = result["TN"]
    fn = result["FN"]

    precision = (
        tp / (tp + fp)
        if tp + fp > 0 else 0
    )

    recall = (
        tp / (tp + fn)
        if tp + fn > 0 else 0
    )

    print(
        f"{strategy:<10}"
        f"{tp:<5}"
        f"{fp:<5}"
        f"{tn:<5}"
        f"{fn:<5}"
        f"{precision:<12.2f}"
        f"{recall:<10.2f}"
    )

print("\n✅ EXPERIMENT 08 COMPLETE")
