import csv
import json
from pathlib import Path

DATASET = Path(__file__).resolve().parent.parent / "dataset"

def load_csv(filename):
    with (DATASET / filename).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

expected = {r["case_id"]: r for r in load_csv("sample_output.csv")}
actual = {r["case_id"]: r for r in load_csv("output.csv")}

status_correct = 0
exact_correct = 0

for case_id, row in expected.items():
    result = actual.get(case_id)

    if result is None:
        print(case_id, "| MISSING")
        continue

    status_match = result["deletion_status"] == row["deletion_status"]
    steps_match = json.loads(result["steps_json"]) == json.loads(row["steps_json"])

    status_correct += int(status_match)
    exact_correct += int(status_match and steps_match)

    if not (status_match and steps_match):
        print(case_id, "| Expected:", row["deletion_status"],
              "| Actual:", result["deletion_status"],
              "| Expected steps:", len(json.loads(row["steps_json"])),
              "| Actual steps:", len(json.loads(result["steps_json"])))

print("\n=== RESULTS ===")
print("Sample cases:", len(expected))
print("Correct statuses:", f"{status_correct}/{len(expected)}")
print("Exact matches:", f"{exact_correct}/{len(expected)}")
