
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"


def load_csv(filename):
    with (DATASET / filename).open(
        encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))


def main():
    expected = {
        row["case_id"]: row
        for row in load_csv("sample_output.csv")
    }

    actual = {
        row["case_id"]: row
        for row in load_csv("output.csv")
    }

    status_correct = 0
    exact_correct = 0

    print("\n=== SAMPLE EVALUATION ===")

    for case_id, expected_row in expected.items():
        actual_row = actual.get(case_id)

        if actual_row is None:
            print(case_id, "| MISSING")
            continue

        status_match = (
            actual_row["deletion_status"]
            == expected_row["deletion_status"]
        )

        expected_steps = json.loads(expected_row["steps_json"])
        actual_steps = json.loads(actual_row["steps_json"])

        exact_match = (
            status_match and actual_steps == expected_steps
        )

        status_correct += int(status_match)
        exact_correct += int(exact_match)

        if not exact_match:
            print(
                case_id,
                "| Expected:", expected_row["deletion_status"],
                "| Actual:", actual_row["deletion_status"],
                "| Expected steps:", len(expected_steps),
                "| Actual steps:", len(actual_steps),
            )

    total = len(expected)

    print("\n=== RESULTS ===")
    print("Sample cases:", total)
    print("Correct statuses:", f"{status_correct}/{total}")
    print("Exact matches:", f"{exact_correct}/{total}")


if __name__ == "__main__":
    main()
