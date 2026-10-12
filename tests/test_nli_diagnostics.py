import numpy as np
from sentence_transformers import CrossEncoder

MODEL = "cross-encoder/nli-deberta-v3-small"

print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 07: NLI DIAGNOSTICS")
print("=" * 55)

model = CrossEncoder(MODEL)

print("\nMODEL CONFIGURATION")
print("Model:", MODEL)
print("Labels:", model.model.config.id2label)
print("Number of labels:", model.model.config.num_labels)

labels = {
    int(k): str(v).lower()
    for k, v in model.model.config.id2label.items()
}

def analyze(premise, hypothesis):
    logits = np.asarray(
        model.predict(
            [(premise, hypothesis)],
            apply_softmax=False
        )
    ).reshape(-1)

    shifted = logits - np.max(logits)
    probabilities = np.exp(shifted)
    probabilities /= probabilities.sum()

    winner = int(np.argmax(probabilities))

    return {
        "prediction": labels[winner],
        "probabilities": {
            labels[i]: round(float(p), 4)
            for i, p in enumerate(probabilities)
        }
    }


experiments = [
    (
        "IDENTICAL",
        "Asym uses Python.",
        "Asym uses Python."
    ),
    (
        "ENTAILMENT",
        "Asym uses Python and JavaScript.",
        "Asym uses Python."
    ),
    (
        "CONTRADICTION",
        "Asym uses Python.",
        "Asym does not use Python."
    ),
    (
        "UNRELATED",
        "Asym uses Python.",
        "The Atlantic Ocean contains salt water."
    ),
    (
        "DIFFERENT SUBJECTS",
        "MemoryOS uses SQLite.",
        "ReasoningOS uses PostgreSQL."
    ),
    (
        "NUMERICAL",
        "The project has exactly 10 users.",
        "The project has exactly 100 users."
    ),
    (
        "PARAPHRASE",
        "The application stores information permanently.",
        "The software retains data across restarts."
    ),
    (
        "PARTIAL INFORMATION",
        "Asym uses Python.",
        "Asym uses Python and JavaScript."
    )
]

for name, first, second in experiments:
    print(f"\n🔬 TEST: {name}")
    print("-" * 45)

    forward = analyze(first, second)
    backward = analyze(second, first)

    print("Forward:", forward["prediction"])
    print("Scores:", forward["probabilities"])

    print("Backward:", backward["prediction"])
    print("Scores:", backward["probabilities"])

    print(
        "Order changes prediction:",
        forward["prediction"] != backward["prediction"]
    )

print("\n✅ EXPERIMENT 07 COMPLETE")
