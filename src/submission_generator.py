
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"


def load_requests():
    path = DATASET / "deletion_requests.csv"

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def validate_step(step):
    required_fields = {
        "step_no",
        "phase",
        "system_id",
        "resource_id",
        "operation",
        "state",
        "evidence_id",
    }

    if set(step) != required_fields:
        raise ValueError("Invalid step fields")

    if step["phase"] not in {
        "FINDING",
        "REMEDIATION",
        "VERIFICATION",
    }:
        raise ValueError("Invalid phase")


def validate_result(status, steps):
    if status not in {
        "COMPLETE",
        "INCOMPLETE",
        "NOT_APPLICABLE",
    }:
        raise ValueError("Invalid deletion status")

    if status == "NOT_APPLICABLE" and steps:
        raise ValueError("NOT_APPLICABLE must have no steps")

    if status == "COMPLETE" and any(
        step["phase"] != "VERIFICATION" for step in steps
    ):
        raise ValueError("COMPLETE must contain verification only")

    for number, step in enumerate(steps, start=1):
        validate_step(step)

        if step["step_no"] != number:
            raise ValueError("Incorrect step numbering")


def generate_output(evaluate_case):
    requests = sorted(
        load_requests(),
        key=lambda row: row["case_id"]
    )

    if len(requests) != 518:
        raise ValueError(
            f"Expected 518 cases, found {len(requests)}"
        )

    rows = []

    for request in requests:
        status, steps = evaluate_case(request)
        validate_result(status, steps)

        rows.append({
            "case_id": request["case_id"],
            "deletion_status": status,
            "steps_json": json.dumps(
                steps,
                separators=(",", ":")
            ),
        })

    output_path = DATASET / "output.csv"

    with output_path.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "case_id",
                "deletion_status",
                "steps_json",
            ]
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} cases")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    print("Submission generator loaded successfully.")
    print("Cases available:", len(load_requests()))
    print("Evidence-based evaluator still needs to be connected.")
