import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_knowledge_base import validate  # noqa: E402


def test_every_class_has_a_valid_entry(class_names):
    diseases = json.loads((ROOT / "data" / "diseases.json").read_text())
    assert validate(class_names, diseases) == []


def test_validator_catches_missing_class(class_names):
    assert any("missing entry" in problem for problem in validate(class_names, {}))
