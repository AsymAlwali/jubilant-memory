from memoryos.grounding import MemoryGroundingEngine
from memoryos.resolution import IntegratedResolutionEngine


class GroundedResolutionEngine(IntegratedResolutionEngine):
    """
    Resolve recorded conflicts using observations derived
    from the original stored memories.

    The caller supplies transition evidence, but cannot
    directly supply or replace the observations.

    Grounding verifies correspondence to stored records,
    not factual truth or evidence authenticity.
    """

    def __init__(self, db_path):
        super().__init__(db_path)
        self.grounding = MemoryGroundingEngine(db_path)

    def submit_grounded_evidence(
        self,
        conflict_id,
        content,
        event,
        source=None
    ):
        conflict = self.get_conflict(conflict_id)

        if conflict is None:
            raise ValueError("Conflict does not exist")

        memory_ids = [
            conflict["existing_id"],
            conflict["incoming_id"]
        ]

        observations = []

        for memory_id in memory_ids:

            result = self.grounding.get_grounded_observation(
                memory_id
            )

            if result["status"] != "grounded":
                return {
                    "accepted": False,
                    "status": "grounding_failed",
                    "memory_id": memory_id,
                    "grounding_status": result["status"],
                    "review_id": None
                }

            observations.append(result["observation"])

        # Ensure we actually grounded two distinct memories.
        if len({item["memory_id"] for item in observations}) != 2:
            return {
                "accepted": False,
                "status": "invalid_conflict",
                "review_id": None
            }

        # Reuse the existing temporal validator and
        # evidence-review persistence workflow.
        result = self.submit_evidence(
            conflict_id=conflict_id,
            content=content,
            event=event,
            observations=observations,
            source=source
        )

        return {
            **result,
            "grounded_memory_ids": memory_ids,
            "grounding_status": "grounded"
        }

    def close(self):
        self.grounding.close()
        super().close()
