
from audit_agent import detect_deletion_request
from identity_resolver import resolve_identity
from database_reader import find_user_records
from resource_evaluator import evaluate_resource


def evaluate_case(request):
    case_id = request["case_id"]
    email = request["email"]
    audit_at = request["audit_at"]
    request_text = request["request_text"]

    if not detect_deletion_request(request_text):
        return "NOT_APPLICABLE", []

    identity = resolve_identity(email)

    user_ids = identity["user_ids"]
    emails = identity["emails"]

    # Temporary snapshot for integration testing
    evidence_id = "evidence_05"

    records = find_user_records(
        evidence_id,
        user_ids,
        emails,
    )

    unique_records = {
        record["resource_id"]: record
        for record in records
    }

    results = []

    for record in unique_records.values():
        result = evaluate_resource(record, audit_at)
        results.append(result)

    incomplete = any(
        result["status"] == "INCOMPLETE"
        for result in results
    )

    if not results:
        status = "INCOMPLETE"
    elif incomplete:
        status = "INCOMPLETE"
    else:
        status = "COMPLETE"

    print(
        case_id,
        "|",
        status,
        "| Resources:",
        len(results),
    )

    return status, []
