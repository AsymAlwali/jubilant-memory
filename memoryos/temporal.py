from datetime import datetime, timezone


class TemporalEvidenceValidator:
    """
    Validate observations against structured transition evidence.

    Assumptions:
    - A single subject and attribute.
    - One instantaneous transition.
    - The old value applies before the effective time.
    - The new value applies at and after the effective time.
    - Dates without times represent midnight UTC.

    This checks consistency, not evidence authenticity.
    """

    @staticmethod
    def _parse_time(value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Timestamp must be a nonempty string")

        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError as error:
            raise ValueError(
                f"Invalid ISO timestamp: {value}"
            ) from error

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    def validate_observation(self, observation, event):

        required_observation = {
            "subject", "attribute", "value", "valid_at"
        }

        required_event = {
            "subject", "attribute", "old_value",
            "new_value", "effective_at"
        }

        missing_observation = (
            required_observation - observation.keys()
        )

        missing_event = (
            required_event - event.keys()
        )

        if missing_observation:
            raise ValueError(
                f"Missing observation fields: {missing_observation}"
            )

        if missing_event:
            raise ValueError(
                f"Missing event fields: {missing_event}"
            )

        if (
            observation["subject"] != event["subject"]
            or observation["attribute"] != event["attribute"]
        ):
            return {
                "status": "not_applicable",
                "consistent": None,
                "reason": (
                    "Evidence describes a different "
                    "subject or attribute."
                )
            }

        observed_at = self._parse_time(
            observation["valid_at"]
        )

        effective_at = self._parse_time(
            event["effective_at"]
        )

        if observed_at < effective_at:
            expected_value = event["old_value"]
            period = "before_transition"
        else:
            expected_value = event["new_value"]
            period = "after_transition"

        actual_value = observation["value"]

        consistent = actual_value == expected_value

        return {
            "status": (
                "consistent"
                if consistent
                else "inconsistent"
            ),
            "consistent": consistent,
            "period": period,
            "expected_value": expected_value,
            "observed_value": actual_value,
            "reason": (
                "Observation matches transition evidence."
                if consistent
                else "Observation disagrees with transition evidence."
            )
        }

    def evaluate_explanation(
        self,
        observations,
        event
    ):
        """
        Evaluate whether a transition event consistently
        explains a collection of observations.

        A valid explanation requires:
        - At least two observations.
        - All observations to be applicable.
        - All observations to be consistent.
        - Observations on both sides of the transition.
        """

        if len(observations) < 2:
            return {
                "status": "insufficient_evidence",
                "explains": False,
                "reason": "At least two observations are required.",
                "results": []
            }

        results = [
            self.validate_observation(item, event)
            for item in observations
        ]

        applicable = all(
            result["status"] != "not_applicable"
            for result in results
        )

        consistent = all(
            result["consistent"] is True
            for result in results
        )

        periods = {
            result.get("period")
            for result in results
        }

        covers_transition = {
            "before_transition",
            "after_transition"
        }.issubset(periods)

        explains = (
            applicable
            and consistent
            and covers_transition
        )

        if not applicable:
            status = "not_applicable"
        elif not consistent:
            status = "inconsistent"
        elif not covers_transition:
            status = "insufficient_evidence"
        else:
            status = "explanation_candidate"

        return {
            "status": status,
            "explains": explains,
            "results": results,
            "reason": (
                "Observations are consistent with the "
                "proposed transition."
                if explains
                else "The proposed transition does not fully "
                     "explain the observations."
            )
        }
