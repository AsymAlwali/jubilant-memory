from memoryos.pipeline import MemoryPipeline
from memoryos.resolution import IntegratedResolutionEngine


class ResolutionAwareRecall:
    """
    Combines semantic memory retrieval with recorded
    conflict-resolution decisions.

    An 'explained' status means a reviewer accepted
    an explanation. It does not prove the explanation
    is factually correct.
    """

    def __init__(self, db_path):
        self.memory = MemoryPipeline(db_path)
        self.resolution = IntegratedResolutionEngine(db_path)

    def recall_with_resolutions(self, query, limit=5):

        memories = self.memory.recall(
            query,
            limit=limit
        )

        results = []

        for memory in memories:

            memory_id = memory["id"]

            conflict_rows = self.resolution.db.execute("""
                SELECT
                    id,
                    existing_id,
                    incoming_id
                FROM conflicts
                WHERE existing_id = ?
                   OR incoming_id = ?
                ORDER BY created_at, rowid
            """, (
                memory_id,
                memory_id
            )).fetchall()

            conflicts = []

            for conflict_id, existing_id, incoming_id in conflict_rows:

                other_id = (
                    incoming_id
                    if existing_id == memory_id
                    else existing_id
                )

                other_row = self.resolution.db.execute("""
                    SELECT content
                    FROM memories
                    WHERE id = ?
                """, (other_id,)).fetchone()

                review_rows = self.resolution.db.execute("""
                    SELECT
                        r.id,
                        r.explanation,
                        r.status,
                        r.reviewer,
                        e.source
                    FROM resolution_reviews r
                    JOIN resolution_evidence e
                        ON r.evidence_id = e.id
                    WHERE r.conflict_id = ?
                    ORDER BY r.created_at, r.rowid
                """, (conflict_id,)).fetchall()

                reviews = []

                for (
                    review_id,
                    explanation,
                    review_status,
                    reviewer,
                    evidence_source
                ) in review_rows:

                    reviews.append({
                        "review_id": review_id,
                        "explanation": explanation,
                        "status": review_status,
                        "reviewer": reviewer,
                        "evidence_source": evidence_source
                    })

                accepted_reviews = [
                    review
                    for review in reviews
                    if review["status"] == "explained"
                ]

                conflict_status = (
                    "explained"
                    if accepted_reviews
                    else "disputed"
                )

                conflicts.append({
                    "conflict_id": conflict_id,
                    "other_memory_id": other_id,
                    "other_memory_content": (
                        other_row[0]
                        if other_row
                        else None
                    ),
                    "status": conflict_status,
                    "reviews": reviews,
                    "accepted_explanations": accepted_reviews
                })

            if not conflicts:
                overall_status = "no_recorded_conflict"

            elif all(
                conflict["status"] == "explained"
                for conflict in conflicts
            ):
                overall_status = "explained"

            else:
                overall_status = "disputed"

            results.append({
                **memory,
                "status": overall_status,
                "conflict_count": len(conflicts),
                "conflicts": conflicts
            })

        return results

    def close(self):
        self.resolution.close()
        self.memory.close()
