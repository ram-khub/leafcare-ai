"""SDG Impact: how early crop-disease detection supports SDG 2 (and SDG 12)."""

import streamlit as st

from utils import ui

FAO_SOURCE = "https://www.fao.org/newsroom/detail/New-standards-to-curb-the-global-spread-of-plant-pests-and-diseases/en"

ui.page_header(
    "Why it matters",
    "Fighting hunger, one leaf at a time",
    "Early, accurate disease detection helps farmers save more of what they grow and use fewer "
    "chemicals doing it.",
)

ui.stat_tiles([
    ("Crop loss / year", "20–40%"),
    ("Disease cost / year", "$220 bn"),
    ("Known conditions", "38"),
    ("Crops covered", "14"),
])
st.caption(f"Loss and cost figures: [FAO]({FAO_SOURCE}).")

st.write("")
st.html("""
<div class="lc-grid-2">
  <div class="lc-card">
    <span class="lc-sdg-badge"><b>SDG 2</b> Zero Hunger</span>
    <h3>Target 2.4: sustainable, resilient food production</h3>
    <p>
      Target 2.4 asks for farming practices that raise productivity while protecting ecosystems.
      Plant diseases work against both: a blight noticed a week too late can wipe out a field,
      and the usual response, spraying everything, harms soil and water.
    </p>
    <p>
      LeafCare AI gives a first opinion in seconds from an ordinary phone photo, so problems are
      noticed <b>earlier</b>, when they are cheaper and easier to control, and a crop's yield is protected.
    </p>
  </div>
  <div class="lc-card">
    <span class="lc-sdg-badge lc-sdg-12"><b>SDG 12</b> Responsible Consumption</span>
    <h3>Fewer, better-targeted chemicals</h3>
    <p>
      When farmers can't tell diseases apart, they often use the wrong product or too much of it,
      just in case. Knowing <b>which</b> disease is present means treating only what is needed,
      starting with cultural and organic measures.
    </p>
    <p>
      That supports responsible chemical management and reduces food lost before harvest,
      both central aims of SDG 12.
    </p>
  </div>
</div>
""")

st.write("")
st.subheader("How LeafCare AI helps")
ui.steps([
    ("Detect early", "Spot disease from a photo before it spreads across the field."),
    ("Understand", "See the crop, the likely disease, and a heatmap showing why."),
    ("Act responsibly", "Get prevention-first advice and a reminder to consult local experts."),
])

st.subheader("Who could benefit")
st.markdown(
    "- **Smallholder farmers**, who produce a large share of the world's food but often have "
    "limited access to plant-health experts.\n"
    "- **Extension workers**, as a quick triage tool to prioritise field visits.\n"
    "- **Students and home gardeners** learning to recognise common crop diseases."
)

st.subheader("Using AI responsibly")
ui.callout("warn", "⚖️", "A first opinion, not a final diagnosis",
           "The model was trained on lab-style photos and only knows 38 conditions. It flags uncertain "
           "results, explains where it looked, and always recommends confirming with a local "
           "agricultural officer before applying chemicals.")
