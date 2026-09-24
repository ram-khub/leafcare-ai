"""Feedback: a simple form. Placeholder only; submissions are not stored or sent anywhere."""

import streamlit as st

from utils import ui
from utils.i18n import t

TOPICS = ["general", "wrong", "bug", "idea"]

ui.page_header(t("feedback.eyebrow"), t("feedback.title"), t("feedback.subtitle"))

with st.container(key="card_feedback"):
    with st.form("feedback", clear_on_submit=True, border=False):
        name_col, email_col = st.columns(2)
        name_col.text_input(t("feedback.name"), placeholder=t("feedback.name_placeholder"))
        email_col.text_input(t("feedback.email"), placeholder=t("feedback.email_placeholder"),
                             help=t("feedback.email_help"))
        st.selectbox(t("feedback.topic"), TOPICS, format_func=lambda topic: t(f"feedback.topic_{topic}"))
        st.text_area(t("feedback.message"), placeholder=t("feedback.message_placeholder"), height=160)
        sent = st.form_submit_button(t("feedback.send"), type="primary", icon=":material/send:")

if sent:
    ui.callout("info", "✅", t("feedback.received_title"), t("feedback.received_body"))
