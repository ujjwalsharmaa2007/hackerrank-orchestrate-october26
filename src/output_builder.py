
ACTION_CONFIG = {
    "DELETE": {
        "finding": ("REPORT_REMAINING_RECORD", "PRESENT"),
        "remediation": ("DELETE_RECORD", "ABSENT"),
        "verification": ("VERIFY_RECORD_ABSENT", "ABSENT"),
    },
    "REDACT": {
        "finding": ("REPORT_EXPOSED_PII", "PRESENT"),
        "remediation": ("REDACT_RECORD", "REDACTED"),
        "verification": ("VERIFY_RECORD_REDACTED", "REDACTED"),
    },
    "ANONYMIZE": {
        "finding": ("REPORT_EXPOSED_PII", "PRESENT"),
        "remediation": ("ANONYMIZE_RECORD", "ANONYMIZED"),
        "verification": ("VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"),
    },
    "DISABLE_FLOW": {
        "finding": ("REPORT_ACTIVE_DATA_FLOW", "ACTIVE"),
        "remediation": ("DISABLE_DATA_FLOW", "DISABLED"),
        "verification": ("VERIFY_DATA_FLOW_DISABLED", "DISABLED"),
    },
    "RETAIN": {
        "verification": ("VERIFY_RECORD_PRESENT", "PRESENT"),
    },
}


def build_steps(resource_results):
    steps = []

    incomplete = any(
        result["status"] == "INCOMPLETE"
        for result in resource_results
    )

    def add_step(phase, result, operation, state):
        steps.append({
            "step_no": len(steps) + 1,
            "phase": phase,
            "system_id": result["system_id"],
            "resource_id": result["resource_id"],
            "operation": operation,
            "state": state,
            "evidence_id": result["evidence_id"],
        })

    if incomplete:
        # FINDING steps
        for result in resource_results:
            if result["status"] != "INCOMPLETE":
                continue

            config = ACTION_CONFIG.get(
                result.get("required_action"), {}
            )

            if "finding" in config:
                operation, state = config["finding"]
                add_step("FINDING", result, operation, state)

        # REMEDIATION steps
        for result in resource_results:
            if result["status"] != "INCOMPLETE":
                continue

            config = ACTION_CONFIG.get(
                result.get("required_action"), {}
            )

            if "remediation" in config:
                operation, state = config["remediation"]
                add_step("REMEDIATION", result, operation, state)

    # VERIFICATION steps
    for result in resource_results:
        config = ACTION_CONFIG.get(
            result.get("required_action"), {}
        )

        if "verification" in config:
            operation, state = config["verification"]
            add_step("VERIFICATION", result, operation, state)

    return steps
