
import csv
from pathlib import Path

# Find the project folder
ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"


def load_csv(filename):
    with (DATASET / filename).open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))


def resolve_identity(email):
    # Load current identities and historical changes
    users = load_csv("user_identities.csv")
    history = load_csv("user_audit_log.csv")

    email = email.strip().lower()

    # Find matching users
    matched_users = []

    for user in users:
        if user["email"].strip().lower() == email:
            matched_users.append(user["user_id"])

    # Also check historical email addresses
    for record in history:
        if record["field_name"].lower() == "email":
            old_email = record["old_value"].strip().lower()
            new_email = record["new_value"].strip().lower()

            if email in (old_email, new_email):
                matched_users.append(record["user_id"])

    matched_users = sorted(set(matched_users))

    # Collect historical emails for matched users
    all_emails = {email}

    for user in users:
        if user["user_id"] in matched_users:
            all_emails.add(user["email"].strip().lower())

    for record in history:
        if (
            record["user_id"] in matched_users
            and record["field_name"].lower() == "email"
        ):
            all_emails.add(record["old_value"].strip().lower())
            all_emails.add(record["new_value"].strip().lower())

    return {
        "user_ids": matched_users,
        "emails": sorted(e for e in all_emails if e)
    }


if __name__ == "__main__":
    result = resolve_identity("ingrid.dahl@outlook.com")

    print("Matched user IDs:", result["user_ids"])
    print("Associated emails:", result["emails"])
