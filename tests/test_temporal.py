from memoryos.temporal import TemporalEvidenceValidator


print("\n🧠 JUBILANT MEMORY")
print("EXPERIMENT 13: STRUCTURED EVIDENCE VALIDATION")
print("=" * 65)

validator = TemporalEvidenceValidator()

event = {
    "subject": "MemoryOS",
    "attribute": "database",
    "old_value": "SQLite",
    "new_value": "PostgreSQL",
    "effective_at": "2026-10-10"
}

cases = [
    (
        "Correct old value",
        {
            "subject": "MemoryOS",
            "attribute": "database",
            "value": "SQLite",
            "valid_at": "2026-10-01"
        },
        "consistent"
    ),
    (
        "Correct new value",
        {
            "subject": "MemoryOS",
            "attribute": "database",
            "value": "PostgreSQL",
            "valid_at": "2026-10-12"
        },
        "consistent"
    ),
    (
        "Wrong value before migration",
        {
            "subject": "MemoryOS",
            "attribute": "database",
            "value": "PostgreSQL",
            "valid_at": "2026-10-01"
        },
        "inconsistent"
    ),
    (
        "Wrong value after migration",
        {
            "subject": "MemoryOS",
            "attribute": "database",
            "value": "SQLite",
            "valid_at": "2026-10-12"
        },
        "inconsistent"
    ),
    (
        "Different project",
        {
            "subject": "ReasoningOS",
            "attribute": "database",
            "value": "SQLite",
            "valid_at": "2026-10-01"
        },
        "not_applicable"
    ),
    (
        "Different attribute",
        {
            "subject": "MemoryOS",
            "attribute": "programming_language",
            "value": "Python",
            "valid_at": "2026-10-01"
        },
        "not_applicable"
    ),
    (
        "Exact migration boundary",
        {
            "subject": "MemoryOS",
            "attribute": "database",
            "value": "PostgreSQL",
            "valid_at": "2026-10-10"
        },
        "consistent"
    ),
    (
        "One second before migration",
        {
            "subject": "MemoryOS",
            "attribute": "database",
            "value": "SQLite",
            "valid_at": "2026-10-09T23:59:59Z"
        },
        "consistent"
    )
]

passed = 0

print("\n1. TESTING INDIVIDUAL OBSERVATIONS")

for name, observation, expected in cases:

    result = validator.validate_observation(
        observation,
        event
    )

    actual = result["status"]
    success = actual == expected

    if success:
        passed += 1

    print(f"\nTEST: {name}")
    print("Expected:", expected)
    print("Actual:", actual)
    print("Result:", "PASS" if success else "FAIL")

print("\n" + "=" * 65)
print("INDIVIDUAL VALIDATION RESULTS")
print(f"Passed: {passed}/{len(cases)}")

assert passed == len(cases)

print("\n2. TESTING COMPLETE EXPLANATION")

before = {
    "subject": "MemoryOS",
    "attribute": "database",
    "value": "SQLite",
    "valid_at": "2026-10-01"
}

after = {
    "subject": "MemoryOS",
    "attribute": "database",
    "value": "PostgreSQL",
    "valid_at": "2026-10-12"
}

result = validator.evaluate_explanation(
    [before, after],
    event
)

print("Status:", result["status"])
print("Explains:", result["explains"])

assert result["status"] == "explanation_candidate"
assert result["explains"] is True

print("\n3. TESTING INCORRECT EXPLANATION")

wrong_event = {
    "subject": "MemoryOS",
    "attribute": "database",
    "old_value": "PostgreSQL",
    "new_value": "SQLite",
    "effective_at": "2026-10-10"
}

result = validator.evaluate_explanation(
    [before, after],
    wrong_event
)

print("Status:", result["status"])
print("Explains:", result["explains"])

assert result["status"] == "inconsistent"
assert result["explains"] is False

print("\n4. TESTING INSUFFICIENT EVIDENCE")

result = validator.evaluate_explanation(
    [before],
    event
)

print("Status:", result["status"])

assert result["status"] == "insufficient_evidence"

print("\n5. TESTING OBSERVATIONS ON ONE SIDE ONLY")

two_old_observations = [
    before,
    {
        "subject": "MemoryOS",
        "attribute": "database",
        "value": "SQLite",
        "valid_at": "2026-10-05"
    }
]

result = validator.evaluate_explanation(
    two_old_observations,
    event
)

print("Status:", result["status"])

assert result["status"] == "insufficient_evidence"

print("\n" + "=" * 65)
print("✅ EXPERIMENT 13 COMPLETE — ALL ASSERTIONS PASSED")
