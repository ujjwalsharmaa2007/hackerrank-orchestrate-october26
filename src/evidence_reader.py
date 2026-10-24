import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"


# Load the list of evidence files
def load_evidence_index():
    path = DATASET / "evidence_files.csv"

    with path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))


# Display basic evidence information
def main():
    evidence = load_evidence_index()

    print("=== EVIDENCE READER ===")
    print("Total evidence entries:", len(evidence))

    print("\nFirst 5 evidence entries:\n")

    for item in evidence[:5]:
        print("Evidence ID:", item["file_id"])
        print("File path:", item["file_path"])
        print("Origin:", item["origin"])
        print("Captured at:", item["captured_at"])

        file_path = DATASET / item["file_path"]

        print("File exists:", file_path.is_file())
        print("-" * 40)


# Search evidence files for a user's email
def search_evidence(email):
    evidence = load_evidence_index()

    print("\n=== SEARCHING EVIDENCE ===")
    print("Searching for:", email)

    matches = []

    for item in evidence:
        file_path = DATASET / item["file_path"]

        if not file_path.is_file():
            continue

        # Search supported text-based files
        if file_path.suffix.lower() not in {
            ".sql", ".log", ".json", ".txt", ".csv"
        }:
            continue

        try:
            with file_path.open(
                "r",
                encoding="utf-8",
                errors="replace"
            ) as file:

                for line_number, line in enumerate(file, 1):
                    if email.lower() in line.lower():
                        matches.append({
                            "evidence_id": item["file_id"],
                            "file": item["file_path"],
                            "line": line_number,
                            "captured_at": item["captured_at"]
                        })

        except OSError as error:
            print("Could not read:", file_path, error)

    return matches


# Run our program
if __name__ == "__main__":
    main()

    results = search_evidence(
        "ingrid.dahl@outlook.com"
    )

    print("\nMatches found:", len(results))

    for result in results[:10]:
        print(result)



def extract_resource_ids(email):
    matches = search_evidence(email)
    resources = set()

    for match in matches:
        file_path = DATASET / match["file"]

        with file_path.open(
            "r", encoding="utf-8", errors="replace"
        ) as file:
            for line_number, line in enumerate(file, 1):
                if line_number == match["line"]:
                    found = re.findall(
                        r"\bresource_id=([A-Za-z0-9_-]+)",
                        line
                    )
                    resources.update(found)
                    break

    return sorted(resources)

if __name__ == "__main__":
    resources = extract_resource_ids(
        "ingrid.dahl@outlook.com"
    )

    print("\n=== DISCOVERED RESOURCES ===")
    print(resources)
