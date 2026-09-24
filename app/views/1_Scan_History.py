"""Scan History: every leaf analysed in this browser session (kept in session state only)."""

from html import escape

import streamlit as st

from utils import i18n, ui
from utils.i18n import t
from utils.predict import split_class_name

ui.page_header(t("history.eyebrow"), t("history.title"), t("history.subtitle"))

history = st.session_state.get("history", [])

if not history:
    ui.callout("info", "🗂️", t("history.empty_title"), t("history.empty_body"))
    st.stop()

diseased = sum(1 for scan in history if scan["severity"] != "none" and not scan["uncertain"])
healthy = sum(1 for scan in history if scan["severity"] == "none" and not scan["uncertain"])
uncertain = sum(1 for scan in history if scan["uncertain"])
ui.stat_tiles([
    (t("history.total"), str(len(history))),
    (t("history.diseased"), str(diseased)),
    (t("history.healthy"), str(healthy)),
    (t("history.uncertain"), str(uncertain)),
])

knowledge_base = i18n.knowledge_base(i18n.current())

for scan in history:
    entry = knowledge_base.get(scan["class_name"])
    crop, disease = (entry["crop"], entry["disease"]) if entry else split_class_name(scan["class_name"])
    with st.container(key=f"card_scan_{scan['id']}"):
        thumb_col, info_col = st.columns([1, 7], gap="small", vertical_alignment="center")
        with thumb_col:
            st.image(scan["thumbnail"], width=110)
        with info_col:
            st.html(f"""
            <div>
              {ui.chip(scan["severity"], scan["uncertain"])}
              <p class="lc-history-title">{escape(crop)} · {escape(disease)}</p>
              <div class="lc-history-meta">{escape(t("history.meta", confidence=ui.format_confidence(scan['confidence']), time=scan["time"]))}</div>
            </div>
            """)

st.write("")
if st.button(t("history.clear"), icon=":material/delete:"):
    st.session_state.history = []
    st.rerun()
