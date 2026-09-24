"""Translations: interface text (app/locales/<lang>.json) and disease advice (data/i18n/diseases.<lang>.json).

English is the source for both. Any key or field missing from a translation falls back to English,
so a partial translation never breaks the app.
"""

import json
from functools import lru_cache
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]
LOCALES_DIR = APP_DIR / "locales"
DATA_DIR = APP_DIR.parent / "data"

# Language code -> name shown in the picker (in that language).
LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी",
    "bn": "বাংলা",
    "mr": "मराठी",
    "te": "తెలుగు",
    "ta": "தமிழ்",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
}
# Language code -> BCP 47 tag for the read-aloud voice (Indian English where the device has it).
SPEECH_TAGS = {"en": "en-IN", "hi": "hi-IN", "bn": "bn-IN", "mr": "mr-IN", "te": "te-IN", "ta": "ta-IN",
               "es": "es-ES", "fr": "fr-FR", "de": "de-DE"}
# Indic scripts: letter-spacing splits their letter clusters and they have no upper case.
INDIC_LANGUAGES = {"hi", "bn", "mr", "te", "ta"}
TRANSLATED_FIELDS = ("crop", "disease", "description", "symptoms", "causes",
                     "treatment_organic", "treatment_chemical", "prevention")


@lru_cache  # not st.cache_data: t() runs dozens of times per page, and that would copy the dict each call
def _strings(lang: str) -> dict[str, str]:
    path = LOCALES_DIR / f"{lang}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


@lru_cache
def knowledge_base(lang: str) -> dict:
    """data/diseases.json with the translated fields of `lang` laid over the English ones."""
    base = json.loads((DATA_DIR / "diseases.json").read_text(encoding="utf-8"))
    path = DATA_DIR / "i18n" / f"diseases.{lang}.json"
    if lang == "en" or not path.exists():
        return base
    translated = json.loads(path.read_text(encoding="utf-8"))
    return {name: {**entry, **{k: v for k, v in translated.get(name, {}).items() if k in TRANSLATED_FIELDS}}
            for name, entry in base.items()}


def current() -> str:
    lang = st.session_state.get("lang", "en")
    return lang if lang in LANGUAGES else "en"


def t(key: str, **values) -> str:
    """The interface string `key` in the current language, with {placeholders} filled in."""
    text = _strings(current()).get(key) or _strings("en")[key]
    return text.format(**values) if values else text


def likely_in_india() -> bool:
    """True when the visitor is probably in India: an Indian language, an -IN browser locale or an IST clock."""
    locale = (st.context.locale or "").upper()
    return current() in INDIC_LANGUAGES or locale.endswith("-IN") or st.context.timezone in {"Asia/Kolkata", "Asia/Calcutta"}


def _initial_language() -> str:
    """?lang= in the URL first, then the browser's language, then English."""
    requested = st.query_params.get("lang", "")
    if requested in LANGUAGES:
        return requested
    browser = (st.context.locale or "").split("-")[0].lower()
    return browser if browser in LANGUAGES else "en"


def language_picker() -> None:
    """The language menu in the header (positioned by .st-key-lang_picker in styles.css)."""
    st.session_state.setdefault("lang", _initial_language())
    with st.container(key="lang_picker"):
        st.selectbox("Language", list(LANGUAGES), format_func=LANGUAGES.get, key="lang",
                     label_visibility="collapsed")
    if current() in INDIC_LANGUAGES:
        st.html("<style>.lc-crop, .lc-section-label, .lc-eyebrow, .lc-stat span, .lc-chip "
                "{ letter-spacing: 0 !important; text-transform: none !important; }</style>")
    # Keep the choice in the URL so a reload or a shared link keeps the language.
    if current() == "en":
        st.query_params.pop("lang", None)
    else:
        st.query_params["lang"] = current()
