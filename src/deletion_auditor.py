
from policy_engine import (
    get_resource_timeline,
    get_deletion_policy
)

from identity_resolver import resolve_identity
from evidence_reader import search_evidence, extract_resource_ids


def audit_resource(resource_id, data_category, audit_at):
    print("=== DELETION AUDITOR ===")
    print("Resource:", resource_id)
    print("Category:", data_category)
    print("Audit time:", audit_at)

    policy = get_deletion_policy(data_category)
    timeline = get_resource_timeline(resource_id, audit_at)

    print("\nApplicable policy:")
    print(policy)

    print("\nResource activity:")

    for event in timeline:
        print(
            event["event_time"],
            event["event_type"],
            event["reported_result"],
            "| Before audit:",
            event["usable_at_audit"]
        )


def audit_user(email, audit_at):
    print("\n=== USER IDENTITY AUDIT ===")
    print("Requested email:", email)

    identity = resolve_identity(email)

    print("Matched user IDs:", identity["user_ids"])
    print("Associated emails:", identity["emails"])
    print("Audit timestamp:", audit_at)

    print("\n=== USER EVIDENCE SEARCH ===")

    all_matches = []

    for associated_email in identity["emails"]:
        matches = search_evidence(associated_email)
        all_matches.extend(matches)

    print("Total evidence matches:", len(all_matches))

    for match in all_matches[:10]:
        print(
            "Evidence:", match["evidence_id"],
            "| File:", match["file"],
            "| Line:", match["line"]
        )

    print("\n=== AUTOMATIC RESOURCE DISCOVERY ===")

    discovered_resources = set()

    for associated_email in identity["emails"]:
        resource_ids = extract_resource_ids(associated_email)
        discovered_resources.update(resource_ids)

    print("Discovered resource IDs:", sorted(discovered_resources))

    for resource_id in sorted(discovered_resources):
        print("\nResource:", resource_id)

        timeline = get_resource_timeline(resource_id, audit_at)

        for event in timeline:
            print(
                "Event:", event["event_type"],
                "| Result:", event["reported_result"],
                "| Before audit:", event["usable_at_audit"]
            )

    return identity


if __name__ == "__main__":
    audit_user(
        email="ingrid.dahl@outlook.com",
        audit_at="2026-07-19T13:00:00Z"
    )

    print()

    audit_resource(
        resource_id="search_2352",
        data_category="SEARCH_INDEX_ENTRY",
        audit_at="2026-07-19T13:00:00Z"
    )
