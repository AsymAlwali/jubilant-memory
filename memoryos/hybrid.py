import numpy as np
from sentence_transformers import SentenceTransformer

from memoryos.relationships import RelationshipEngine


class HybridRelationshipEngine:

    def __init__(self, similarity_threshold=0.65):
        self.embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        self.relationship_engine = RelationshipEngine()
        self.similarity_threshold = similarity_threshold

    def compare(self, existing, incoming):

        vectors = self.embedding_model.encode(
            [existing, incoming],
            normalize_embeddings=True
        )

        similarity = float(
            np.dot(vectors[0], vectors[1])
        )

        if similarity < self.similarity_threshold:
            return {
                "relationship": "unrelated_candidate",
                "similarity": round(similarity, 4),
                "nli_used": False
            }

        result = self.relationship_engine.classify(
            existing,
            incoming
        )

        return {
            "relationship": result["relationship"],
            "similarity": round(similarity, 4),
            "nli_used": True,
            "contradiction_score": result["contradiction_score"],
            "mutual_entailment_score": result["mutual_entailment_score"]
        }
