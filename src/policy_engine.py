
import csv
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"


def parse_time(value):
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def get_resource_timeline(resource_id, audit_at):
    activity_file = DATASET / "system_activity.csv"
    audit_time = parse_time(audit_at)

    history = []

    with activity_file.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["resource_id"] != resource_id:
                continue

            event_time = parse_time(row["event_time"])

            history.append({
                "activity_id": row["activity_id"],
                "event_time": row["event_time"],
                "event_type": row["event_type"],
                "reported_result": row["reported_result"],
                "usable_at_audit": event_time <= audit_time
            })

    history.sort(key=lambda x: x["event_time"])
    return history


if __name__ == "__main__":
    resource_id = "search_2352"
    audit_at = "2026-07-19T13:00:00Z"

    events = get_resource_timeline(resource_id, audit_at)

    print("=== RESOURCE TIMELINE ===")

    for event in events:
        print("\nEvent:", event["activity_id"])
        print("Time:", event["event_time"])
        print("Type:", event["event_type"])
        print("Result:", event["reported_result"])
        print("Before audit:", event["usable_at_audit"])


def get_deletion_policy(data_category):
    rules_file = DATASET / "deletion_rules.csv"

    with rules_file.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for rule in reader:
            if rule["data_category"] == data_category:
                return {
                    "rule_id": rule["rule_id"],
                    "category": rule["data_category"],
                    "condition": rule["condition"],
                    "required_action": rule["required_action"]
                }

    return None

if __name__ == "__main__":
    print("\n=== DELETION POLICY TEST ===")
    policy = get_deletion_policy("SEARCH_INDEX_ENTRY")
    print(policy)


def category_from_collection(collection_name):
    mapping = {
        "customer_analytics_reports": "ANALYTICS_PROFILE",
        "security_audit_events": "SECURITY_AUDIT_LOG",
        "customer_search_documents": "SEARCH_INDEX_ENTRY",
        "support_conversations": "SUPPORT_MESSAGE",
        "customer_profiles_primary": "USER_PROFILE",
        "customer_profiles_failover_replica": "USER_PROFILE",
    }

    return mapping.get(collection_name)
