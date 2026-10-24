
import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"


def load_sql_evidence(evidence_id):
    with (DATASET / "evidence_files.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        evidence_files = list(csv.DictReader(file))

    item = next(
        (
            row for row in evidence_files
            if row["file_id"] == evidence_id
        ),
        None
    )

    if item is None:
        raise ValueError(f"Unknown evidence ID: {evidence_id}")

    path = DATASET / item["file_path"]

    if path.suffix.lower() != ".sql":
        raise ValueError("Evidence file is not SQL")

    connection = sqlite3.connect(":memory:")

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
            if table not in {
                "customer_data_primary",
                "customer_data_read_replica",
            }:
                continue

            rows = connection.execute(
                f'SELECT resource_id, origin_system, '
                f'collection_name, record_json, updated_at '
                f'FROM "{table}"'
            )

            for row in rows:
                records.append({
                    "evidence_id": evidence_id,
                    "table": table,
                    "resource_id": row[0],
                    "origin_system": row[1],
                    "collection_name": row[2],
                    "record": json.loads(row[3]),
                    "updated_at": row[4],
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

    matches = []

    for record in records:
        if contains_identifier(record["record"]):
            matches.append(record)

    return matches


if __name__ == "__main__":
    records = load_sql_evidence("evidence_05")

    print("Evidence:", "evidence_05")
    print("Records loaded:", len(records))

    for record in records[:3]:
        print(
            "Resource:", record["resource_id"],
            "| System:", record["origin_system"],
            "| Collection:", record["collection_name"],
        )
