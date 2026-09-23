"""Check that data/diseases.json has a complete, well-formed entry for every model class.

Run from the project root:  python scripts/validate_knowledge_base.py
Exits with code 1 (and lists every problem) if anything is wrong.
Re-run it after copying a new class_names.json from Colab.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASS_NAMES_PATH = ROOT / "models" / "class_names.json"
DISEASES_PATH = ROOT / "data" / "diseases.json"

REQUIRED_FIELDS = {
    "crop": str,
    "disease": str,
    "is_healthy": bool,
    "severity": str,
    "description": str,
    "symptoms": list,
    "causes": str,
    "treatment_organic": list,
    "treatment_chemical": list,
    "prevention": list,
    "source": str,
}
SEVERITIES = {"none", "moderate", "severe"}


def check_entry(name: str, entry: dict) -> list[str]:
    """Problems with a single knowledge-base entry."""
    problems = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in entry:
            problems.append(f"{name}: missing field '{field}'")
        elif not isinstance(entry[field], expected_type):
            problems.append(f"{name}: '{field}' should be {expected_type.__name__}")
    if problems:
        return problems  # content checks below assume the structure is right

    if entry["severity"] not in SEVERITIES:
        problems.append(f"{name}: severity must be one of {sorted(SEVERITIES)}")
    if entry["is_healthy"] != (entry["severity"] == "none"):
        problems.append(f"{name}: healthy classes need severity 'none' (and only they)")
    lists_to_fill = ["prevention"]
    if not entry["is_healthy"]:
        lists_to_fill += ["symptoms", "treatment_organic", "treatment_chemical"]
    for field in lists_to_fill:
        if not entry[field]:
            problems.append(f"{name}: '{field}' is empty")
    if not entry["source"].startswith("https://"):
        problems.append(f"{name}: source should be an https:// URL")
    return problems


def validate(class_names: list[str], diseases: dict) -> list[str]:
    """Return a list of human-readable problems (empty list = all good)."""
    problems = [f"missing entry for class '{name}'" for name in class_names if name not in diseases]
    problems += [
        f"entry '{name}' does not match any class in class_names.json"
        for name in diseases if name not in class_names
    ]
    for name, entry in diseases.items():
        problems += check_entry(name, entry)
    return problems


def main() -> None:
    class_names = json.loads(CLASS_NAMES_PATH.read_text())
    diseases = json.loads(DISEASES_PATH.read_text())
    problems = validate(class_names, diseases)
    if problems:
        print(f"Knowledge base has {len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        sys.exit(1)
    print(f"OK: all {len(class_names)} classes have a complete knowledge-base entry.")


if __name__ == "__main__":
    main()
