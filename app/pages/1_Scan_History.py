"""Scan History: every leaf analysed in this browser session (kept in session state only)."""

from html import escape

import streamlit as st

from utils import ui

ui.page_header(
    "Your session",
    "Scan history",
    "Leaves you have analysed since opening the app. Nothing is stored on a server; "
    "the history disappears when you close or refresh the page.",
)

history = st.session_state.get("history", [])

if not history:
    ui.callout("info", "🗂️", "No scans yet", "Open Diagnose in the menu at the top, analyse a leaf, and it will appear here.")
    st.stop()

diseased = sum(1 for scan in history if scan["severity"] != "none" and not scan["uncertain"])
healthy = sum(1 for scan in history if scan["severity"] == "none" and not scan["uncertain"])
uncertain = sum(1 for scan in history if scan["uncertain"])
ui.stat_tiles([
    ("Total scans", str(len(history))),
    ("Diseased", str(diseased)),
    ("Healthy", str(healthy)),
    ("Uncertain", str(uncertain)),
])

for scan in history:
    with st.container(key=f"card_scan_{scan['id']}"):
        thumb_col, info_col = st.columns([1, 7], gap="small", vertical_alignment="center")
        with thumb_col:
            st.image(scan["thumbnail"], width=110)
        with info_col:
            st.html(f"""
            <div>
              {ui.chip(scan["severity"], scan["uncertain"])}
              <p class="lc-history-title">{escape(scan["crop"])} · {escape(scan["disease"])}</p>
              <div class="lc-history-meta">Confidence {scan["confidence"]:.1%} &nbsp;·&nbsp; Scanned at {scan["time"]}</div>
            </div>
            """)

st.write("")
if st.button("Clear history", icon=":material/delete:"):
    st.session_state.history = []
    st.rerun()
