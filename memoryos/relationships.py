import numpy as np
from sentence_transformers import CrossEncoder


class RelationshipEngine:
    def __init__(self):
        self.model = CrossEncoder(
            "cross-encoder/nli-deberta-v3-small"
        )

        labels = self.model.model.config.id2label

        self.label_ids = {
            str(label).lower(): int(index)
            for index, label in labels.items()
        }

        required = {
            "contradiction",
            "entailment",
            "neutral"
        }

        if not required.issubset(self.label_ids):
            raise ValueError(
                f"Unexpected NLI labels: {labels}"
            )

    def _predict(self, first, second):
        logits = np.asarray(
            self.model.predict(
                [(first, second)],
                apply_softmax=False
            )
        ).reshape(-1)

        logits = logits - np.max(logits)
        probabilities = np.exp(logits)
        probabilities /= probabilities.sum()

        return {
            label: round(
                float(probabilities[index]), 4
            )
            for label, index in self.label_ids.items()
        }

    def classify(self, existing, incoming):
        forward = self._predict(existing, incoming)
        backward = self._predict(incoming, existing)

        contradiction = max(
            forward["contradiction"],
            backward["contradiction"]
        )

        entailment = min(
            forward["entailment"],
            backward["entailment"]
        )

        if contradiction >= 0.80:
            relationship = "contradiction"

        elif entailment >= 0.80:
            relationship = "equivalent_candidate"

        else:
            relationship = "related_or_unrelated"

        return {
            "relationship": relationship,
            "contradiction_score": contradiction,
            "mutual_entailment_score": entailment,
            "forward": forward,
            "backward": backward
        }
