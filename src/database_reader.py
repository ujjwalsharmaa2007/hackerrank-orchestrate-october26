
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"


def load_evidence_index():
    with (DATASET / "evidence_files.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))


def load_sql_evidence(evidence_id):
    item = next(
        (
            row for row in load_evidence_index()
            if row["file_id"] == evidence_id
        ),
        None,
    )

    if item is None:
        raise ValueError(f"Unknown evidence ID: {evidence_id}")

    path = DATASET / item["file_path"]

    if path.suffix.lower() != ".sql":
        raise ValueError("Evidence file is not SQL")

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    try:
        connection.executescript(
            path.read_text(encoding="utf-8-sig")
        )

        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table'"
            )
        ]

        records = []

        for table in tables:
            rows = connection.execute(
                f'SELECT * FROM "{table}"'
            )

            for row in rows:
                raw = dict(row)

                if "record_json" in raw:
                    try:
                        record = json.loads(raw["record_json"])
                    except (ValueError, TypeError):
                        record = raw
                else:
                    record = raw

                resource_id = (
                    raw.get("resource_id")
                    or record.get("resource_id")
                )

                if not resource_id:
                    continue

                records.append({
                    "evidence_id": evidence_id,
                    "table": table,
                    "resource_id": resource_id,
                    "origin_system": (
                        raw.get("origin_system")
                        or table
                    ),
                    "collection_name": (
                        raw.get("collection_name")
                        or table
                    ),
                    "record": record,
                    "updated_at": raw.get("updated_at", ""),
                    "captured_at": item["captured_at"],
                })

        return records

    finally:
        connection.close()


def find_user_records(evidence_id, user_ids, emails):
    records = load_sql_evidence(evidence_id)

    identifiers = {
        str(value).strip().lower()
        for value in user_ids + emails
        if value
    }

    def contains_identifier(value):
        if isinstance(value, dict):
            return any(
                contains_identifier(item)
                for item in value.values()
            )

        if isinstance(value, list):
            return any(
                contains_identifier(item)
                for item in value
            )

        if isinstance(value, str):
            return value.strip().lower() in identifiers

        return False

    return [
        record for record in records
        if contains_identifier(record["record"])
    ]


def select_sql_evidence(audit_at):
    eligible = [
        item
        for item in load_evidence_index()
        if (
            item["file_path"].lower().endswith(".sql")
            and item["captured_at"] <= audit_at
        )
    ]

    if not eligible:
        return None

    selected = max(
        eligible,
        key=lambda item: item["captured_at"]
    )

    return selected["file_id"]


def find_user_records_across_snapshots(audit_at, user_ids, emails):
    eligible = [
        item
        for item in load_evidence_index()
        if (
            item["file_path"].lower().endswith(".sql")
            and item["captured_at"] <= audit_at
        )
    ]

    eligible.sort(key=lambda item: item["captured_at"])

    all_records = []

    for item in eligible:
        records = find_user_records(
            item["file_id"],
            user_ids,
            emails
        )

        all_records.extend(records)

    return all_records
