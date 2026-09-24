"""Feedback: a simple form. Placeholder only; submissions are not stored or sent anywhere."""

import streamlit as st

from utils import ui

ui.page_header(
    "Tell us",
    "Feedback",
    "Spotted a wrong diagnosis, or have an idea to make LeafCare AI more useful? Let us know.",
)

with st.container(key="card_feedback"):
    with st.form("feedback", clear_on_submit=True, border=False):
        name_col, email_col = st.columns(2)
        name_col.text_input("Name (optional)", placeholder="Your name")
        email_col.text_input("Email (optional)", placeholder="you@example.com",
                             help="Only if you'd like a reply.")
        st.selectbox("Topic", ["General feedback", "Wrong diagnosis", "Bug or problem", "Feature idea"])
        st.text_area("Your feedback", placeholder="What worked, what didn't, what you'd like to see…", height=160)
        sent = st.form_submit_button("Send feedback", type="primary", icon=":material/send:")

if sent:
    ui.callout("info", "✅", "Feedback received", "Thanks for taking the time to help improve LeafCare AI.")
