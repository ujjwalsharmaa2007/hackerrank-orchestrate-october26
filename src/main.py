
import csv
from pathlib import Path

from audit_agent import detect_deletion_request
from identity_resolver import resolve_identity

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"


def load_csv(filename):
    with (DATASET / filename).open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))


def main():
    requests = load_csv("deletion_requests.csv")

    print("=== GHOST DATA AI AGENT ===")
    print("Total requests:", len(requests))

    # Find the first case
    case = requests[0]

    print("\nCase ID:", case["case_id"])
    print("Email:", case["email"])

    # Step 1: Detect deletion intent
    deletion_requested = detect_deletion_request(
        case["request_text"]
    )

    print("Deletion requested:", deletion_requested)

    # Step 2: Resolve identity
    identity = resolve_identity(case["email"])

    print("Matched user IDs:", identity["user_ids"])
    print("Associated emails:", identity["emails"])

    print("\nInitial analysis complete!")


if __name__ == "__main__":
    main()
