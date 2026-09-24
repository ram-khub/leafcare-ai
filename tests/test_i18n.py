"""Every translation must match the English source: same keys, placeholders, markup and list lengths."""

import json
import re

import pytest

from utils.i18n import DATA_DIR, LANGUAGES, LOCALES_DIR, TRANSLATED_FIELDS

OTHER_LANGUAGES = [code for code in LANGUAGES if code != "en"]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def shape(text: str) -> tuple:
    """What must survive translation: {placeholders}, <b> tags, markdown list lines and `code`."""
    return (sorted(re.findall(r"\{\w+\}", text)), text.count("<b>"), text.count("\n"), sorted(re.findall(r"`[^`]+`", text)))


@pytest.mark.parametrize("lang", OTHER_LANGUAGES)
def test_interface_strings_match_english(lang):
    english, translated = load(LOCALES_DIR / "en.json"), load(LOCALES_DIR / f"{lang}.json")
    assert translated.keys() == english.keys()
    for key, text in english.items():
        assert translated[key].strip(), key
        assert shape(translated[key]) == shape(text), key


@pytest.mark.parametrize("lang", OTHER_LANGUAGES)
def test_disease_advice_matches_english(lang):
    english = load(DATA_DIR / "diseases.json")
    translated = load(DATA_DIR / "i18n" / f"diseases.{lang}.json")
    assert translated.keys() == english.keys()
    for name, entry in translated.items():
        assert set(entry) == set(TRANSLATED_FIELDS), name
        for field in TRANSLATED_FIELDS:
            assert type(entry[field]) is type(english[name][field]), (name, field)
            if isinstance(entry[field], list):
                assert len(entry[field]) == len(english[name][field]), (name, field)
                assert all(item.strip() for item in entry[field]), (name, field)
            else:
                assert entry[field].strip(), (name, field)
