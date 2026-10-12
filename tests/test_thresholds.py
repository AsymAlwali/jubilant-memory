from sentence_transformers import SentenceTransformer
from memoryos.relationships import RelationshipEngine
import numpy as np

print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 06: THRESHOLD ANALYSIS")
print("=" * 55)

embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

nli = RelationshipEngine()

# Label meanings:
# equivalent = same factual claim
# contradiction = conflicting claims
# neutral = neither equivalent nor contradictory

cases = [
    (
        "Asym develops software using GitHub Codespaces.",
        "Asym writes code using GitHub Codespaces.",
        "equivalent"
    ),
    (
        "Asym uses GitHub Codespaces.",
        "Asym does not use GitHub Codespaces.",
        "contradiction"
    ),
    (
        "Asym develops software using GitHub Codespaces.",
        "The Atlantic Ocean contains salt water.",
        "neutral"
    ),
    (
        "Asym uses Python.",
        "Asym uses Python and JavaScript.",
        "neutral"
    ),
    (
        "MemoryOS uses SQLite for storage.",
        "MemoryOS no longer uses SQLite for storage.",
        "contradiction"
    ),
    (
        "The project has 10 users.",
        "The project has 100 users.",
        "contradiction"
    ),
    (
        "MemoryOS uses SQLite.",
        "ReasoningOS uses PostgreSQL.",
        "neutral"
    ),
    (
        "The application stores information permanently.",
        "The software retains data across restarts.",
        "equivalent"
    ),
    (
        "The system supports offline mode.",
        "The system does not support offline mode.",
        "contradiction"
    ),
    (
        "Python is a programming language.",
        "Saturn has many moons.",
        "neutral"
    )
]

# Compute embeddings once
sentences = []

for first, second, _ in cases:
    sentences.extend([first, second])

vectors = embedding_model.encode(
    sentences,
    normalize_embeddings=True
)

results = []

print("\nComputing relationship predictions...")

for i, (first, second, expected) in enumerate(cases):
    similarity = float(
        np.dot(vectors[2*i], vectors[2*i+1])
    )

    # NLI runs once per pair, regardless of threshold
    nli_result = nli.classify(first, second)

    relation = nli_result["relationship"]

    if relation == "equivalent_candidate":
        prediction = "equivalent"
    elif relation == "contradiction":
        prediction = "contradiction"
    else:
        prediction = "neutral"

    results.append({
        "similarity": similarity,
        "expected": expected,
        "nli_prediction": prediction
    })

thresholds = [0.40, 0.50, 0.60, 0.65, 0.70, 0.80]

print("\nTHRESHOLD COMPARISON")
print("=" * 65)

print(
    f"{'Threshold':<12}"
    f"{'NLI Calls':<12}"
    f"{'Correct':<12}"
    f"{'Accuracy':<12}"
    f"{'Missed':<10}"
)

for threshold in thresholds:
    correct = 0
    calls = 0
    missed = 0

    for result in results:
        if result["similarity"] >= threshold:
            prediction = result["nli_prediction"]
            calls += 1
        else:
            prediction = "neutral"

            if result["expected"] != "neutral":
                missed += 1

        if prediction == result["expected"]:
            correct += 1

    accuracy = correct / len(results) * 100

    print(
        f"{threshold:<12.2f}"
        f"{calls:<12}"
        f"{correct:<12}"
        f"{accuracy:<12.1f}"
        f"{missed:<10}"
    )

print("\nINDIVIDUAL CASES")
print("=" * 65)

for i, result in enumerate(results, start=1):
    print(
        f"{i}. Similarity={result['similarity']:.4f} "
        f"Expected={result['expected']} "
        f"NLI={result['nli_prediction']}"
    )

print("\nEXPERIMENT 06 COMPLETE")
