"""Status-transition matrix verification for Part 2.3.

Runs the six transition checks referenced by Prompt C2. The expected
pattern is:

    200, 200, 422, 200, 422, 200

Run from the project root:

    .\\.venv\\Scripts\\python.exe -m tests.verify_transitions

Uses TestClient, so no separate uvicorn process is needed. The six checks
walk a single task through the state machine in order, so each check
depends on the state left by the one before it.
"""

from fastapi.testclient import TestClient

from app import storage
from app.main import app

EXPECTED_PATTERN = [200, 200, 422, 200, 422, 200]

# (label, status to PATCH to, expected HTTP code)
CHECKS = [
    ("ToDo -> InProgress", "InProgress", 200),
    ("InProgress -> Done", "Done", 200),
    ("Done -> ToDo (must be blocked)", "ToDo", 422),
    ("Done -> InProgress", "InProgress", 200),
    ("InProgress -> InProgress (same, must be blocked)", "InProgress", 422),
    ("InProgress -> Done", "Done", 200),
]


def main() -> int:
    storage._reset()
    client = TestClient(app)

    created = client.post("/tasks", json={"title": "transition matrix"})
    assert created.status_code == 201, created.status_code
    task_id = created.json()["id"]

    actual: list[int] = []
    failures = 0

    for index, (label, new_status, expected) in enumerate(CHECKS, start=1):
        response = client.patch(f"/tasks/{task_id}", json={"status": new_status})
        actual.append(response.status_code)
        if response.status_code == expected:
            print(f"T{index} PASS  {label}: HTTP {response.status_code}")
        else:
            failures += 1
            print(
                f"T{index} FAIL  {label}: HTTP {response.status_code} "
                f"(expected {expected})"
            )

    print()
    print(f"expected pattern: {EXPECTED_PATTERN}")
    print(f"actual pattern:   {actual}")

    if actual == EXPECTED_PATTERN:
        print("\nTransition matrix matches the expected pattern.")
    else:
        print("\nTransition matrix does NOT match. See Prompt C2 for the fix workflow.")

    storage._reset()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
