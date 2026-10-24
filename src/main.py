
import csv
from pathlib import Path

# Locate the dataset relative to this file
ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"

def load_csv(filename):
    path = DATASET / filename

    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))

def main():
    requests = load_csv("deletion_requests.csv")
    rules = load_csv("deletion_rules.csv")

    print("=== GHOST DATA AI AGENT ===")
    print("Dataset loaded successfully!")
    print("Total requests:", len(requests))
    print("Deletion rules:", len(rules))

    if requests:
        first = requests[0]
        print("\nFirst case:")
        print("Case ID:", first["case_id"])
        print("Reported status:", first["reported_status"])
        print("Audit time:", first["audit_at"])

if __name__ == "__main__":
    main()
