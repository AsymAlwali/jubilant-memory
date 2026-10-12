from datetime import datetime


class ContextEngine:
    """
    Context-aware relationship analysis.

    Metadata must be explicitly supplied.
    This version does not extract context using AI.
    """

    def __init__(self, relationship_engine=None):
        self.relationship_engine = relationship_engine

    def compare(self, existing, incoming):

        required = {"content", "subject", "attribute"}

        for memory in (existing, incoming):
            missing = required - memory.keys()

            if missing:
                raise ValueError(
                    f"Missing memory fields: {missing}"
                )

        # Different subjects are not competing claims
        if existing["subject"] != incoming["subject"]:
            return {
                "relationship": "different_subject",
                "conflict": False,
                "reason": "Memories describe different subjects."
            }

        # Different attributes are not directly competing
        if existing["attribute"] != incoming["attribute"]:
            return {
                "relationship": "different_attribute",
                "conflict": False,
                "reason": "Memories describe different properties."
            }

        old_time = existing.get("valid_at")
        new_time = incoming.get("valid_at")

        # Different known observation times
        if old_time and new_time and old_time != new_time:
            return {
                "relationship": "temporal_change_candidate",
                "conflict": False,
                "reason": "Facts refer to different observation times."
            }

        # Run NLI when context matches
        if self.relationship_engine is not None:

            result = self.relationship_engine.classify(
                existing["content"],
                incoming["content"]
            )

            relationship = result["relationship"]

            if relationship == "contradiction":
                return {
                    "relationship": "potential_conflict",
                    "conflict": True,
                    "reason": "NLI detected a possible contradiction.",
                    "nli": result
                }

            return {
                "relationship": relationship,
                "conflict": False,
                "reason": "No contradiction detected.",
                "nli": result
            }

        return {
            "relationship": "needs_nli",
            "conflict": False,
            "reason": "Context matches; NLI verification needed."
        }
