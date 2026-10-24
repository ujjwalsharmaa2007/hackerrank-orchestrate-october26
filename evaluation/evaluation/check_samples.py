
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"


def load_csv(filename):
    with (DATASET / filename).open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))


def compare_outputs():
    expected = {
        row["case_id"]: row
        for row in load_csv("sample_output.csv")
    }

    actual = {
        row["case_id"]: row
        for row in load_csv("output.csv")
    }

    status_correct = 0
    steps_correct = 0

    for case_id, answer in expected.items():
        prediction = actual.get(case_id)

        if prediction is None:
            print("MISSING:", case_id)
            continue

        if prediction["deletion_status"] == answer["deletion_status"]:
            status_correct += 1
        else:
            print(
                "STATUS MISMATCH:",
                case_id,
                "| Expected:", answer["deletion_status"],
                "| Actual:", prediction["deletion_status"],
            )

        try:
            predicted_steps = json.loads(prediction["steps_json"])
            expected_steps = json.loads(answer["steps_json"])

            if predicted_steps == expected_steps:
                steps_correct += 1
            else:
                print("STEPS MISMATCH:", case_id)
        except (ValueError, TypeError):
            print("INVALID STEPS JSON:", case_id)

    total = len(expected)

    print("\n=== SAMPLE EVALUATION ===")
    print(f"Status accuracy: {status_correct}/{total}")
    print(f"Exact steps match: {steps_correct}/{total}")


if __name__ == "__main__":
    compare_outputs()
