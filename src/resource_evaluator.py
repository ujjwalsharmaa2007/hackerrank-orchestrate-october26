
from policy_engine import (
    get_resource_timeline,
    get_deletion_policy,
    category_from_collection,
)


def evaluate_resource(resource, audit_at):
    resource_id = resource["resource_id"]
    collection = resource["collection_name"]

    category = category_from_collection(collection)

    if category is None:
        return {
            "resource_id": resource_id,
            "status": "UNKNOWN",
            "reason": "No policy mapping available",
        }

    policy = get_deletion_policy(category)

    if policy is None:
        return {
            "resource_id": resource_id,
            "status": "UNKNOWN",
            "reason": "No deletion policy found",
        }

    required_action = policy["required_action"]

    timeline = get_resource_timeline(resource_id, audit_at)

    events = [
        event for event in timeline
        if event["usable_at_audit"]
    ]

    action_to_event = {
        "DELETE": "DELETE_RECORD",
        "REDACT": "REDACT_RECORD",
        "ANONYMIZE": "ANONYMIZE_RECORD",
        "RETAIN": "RETAIN_RECORD",
    }

    expected_event = action_to_event.get(required_action)

    matching_events = [
        event for event in events
        if event["event_type"] == expected_event
    ]

    latest_event = (
        matching_events[-1] if matching_events else None
    )

    if required_action == "RETAIN":
        return {
            "resource_id": resource_id,
            "status": "REVIEW_REQUIRED",
            "required_action": required_action,
            "reason": "Retention conditions must be verified",
        }

    if latest_event is None:
        status = "INCOMPLETE"
        reason = "No matching remediation event found"

    elif latest_event["reported_result"] == "SUCCESS":
        status = "REPORTED_SUCCESS"
        reason = "Remediation was reported successful; verify evidence"

    else:
        status = "INCOMPLETE"
        reason = (
            "Latest remediation event: "
            + latest_event["reported_result"]
        )

    return {
        "resource_id": resource_id,
        "status": status,
        "required_action": required_action,
        "reason": reason,
    }
