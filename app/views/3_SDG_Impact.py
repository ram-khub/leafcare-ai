"""SDG Impact: how early crop-disease detection supports SDG 2 (and SDG 12)."""

import streamlit as st

from utils import ui
from utils.i18n import t

FAO_SOURCE = "https://www.fao.org/newsroom/detail/New-standards-to-curb-the-global-spread-of-plant-pests-and-diseases/en"

ui.page_header(t("sdg.eyebrow"), t("sdg.title"), t("sdg.subtitle"))

ui.stat_tiles([
    (t("sdg.crop_loss"), "20–40%"),
    (t("sdg.disease_cost"), "$220 bn"),
    (t("sdg.conditions"), "38"),
    (t("sdg.crops"), "14"),
])
st.caption(t("sdg.figures_source", url=FAO_SOURCE))

st.write("")
# Translations may contain <b> for emphasis; they are our own files, not user input.
st.html(f"""
<div class="lc-grid-2">
  <div class="lc-card">
    <span class="lc-sdg-badge"><b>SDG 2</b> {t("sdg2.name")}</span>
    <h3>{t("sdg.sdg2_title")}</h3>
    <p>{t("sdg.sdg2_p1")}</p>
    <p>{t("sdg.sdg2_p2")}</p>
  </div>
  <div class="lc-card">
    <span class="lc-sdg-badge lc-sdg-12"><b>SDG 12</b> {t("sdg12.name")}</span>
    <h3>{t("sdg.sdg12_title")}</h3>
    <p>{t("sdg.sdg12_p1")}</p>
    <p>{t("sdg.sdg12_p2")}</p>
  </div>
</div>
""")

st.write("")
st.subheader(t("sdg.helps"))
ui.steps([
    (t("sdg.detect_title"), t("sdg.detect_body")),
    (t("sdg.understand_title"), t("sdg.understand_body")),
    (t("sdg.act_title"), t("sdg.act_body")),
])

st.subheader(t("sdg.who"))
st.markdown(t("sdg.who_body"))

st.subheader(t("sdg.responsible"))
ui.callout("warn", "⚖️", t("sdg.responsible_title"), t("sdg.responsible_body"))
