"""Reusable UI building blocks: CSS injection, hero/header, cards, chips and charts.

All custom HTML uses classes defined in assets/styles.css (prefixed `lc-`).
Text coming from data is escaped with html.escape before being inserted.
"""

import base64
import json
from html import escape
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from utils.i18n import SPEECH_TAGS, current, t

ASSETS = Path(__file__).resolve().parents[1] / "assets"
LOGO_PATH = ASSETS / "logo.svg"

# Colours match assets/styles.css and .streamlit/config.toml.
LEAF, AMBER, RED, GREY, TRACK = "#2F6B3A", "#E0A33B", "#C2412D", "#9AA39C", "#D9D2C1"
# CSS variables (not hex) so the result card follows light/dark mode.
SEVERITY_COLORS = {"none": "var(--leaf)", "moderate": "var(--amber)", "severe": "var(--red)"}


def inject_css() -> None:
    """Load the custom stylesheet into the page (call once per run, from Home.py)."""
    st.html(f"<style>{(ASSETS / 'styles.css').read_text()}</style>")


def page_scripts() -> None:
    """Add the light/dark switch and the read-aloud handler (call once per run, from Home.py)."""
    labels = json.dumps({"toLight": t("theme.to_light"), "toDark": t("theme.to_dark"), "name": t("theme.label")},
                        ensure_ascii=False)
    scripts = "\n".join((ASSETS / name).read_text() for name in ("theme_switch.js", "read_aloud.js"))
    st.html(f"<script>window.__lcThemeLabels = {labels};\n{scripts}</script>", unsafe_allow_javascript=True)


@st.cache_data
def _logo_data_uri() -> str:
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


def hero(title: str, tagline: str) -> None:
    st.html(f"""
    <div class="lc-hero">
      <img src="{_logo_data_uri()}" alt="">
      <div class="lc-hero-text">
        <h1>{escape(title)}</h1>
        <p>{escape(tagline)}</p>
      </div>
      <span class="lc-sdg-badge"><b>SDG 2</b> {escape(t("sdg2.name"))}</span>
    </div>
    """)


def page_header(eyebrow: str, title: str, subtitle: str) -> None:
    st.html(f"""
    <div class="lc-page-header">
      <div class="lc-eyebrow">{escape(eyebrow)}</div>
      <h1>{escape(title)}</h1>
      <p>{escape(subtitle)}</p>
    </div>
    """)


def chip(severity: str, uncertain: bool = False) -> str:
    """HTML for a coloured status chip: healthy (green), moderate (amber), severe (red)."""
    if uncertain:
        return f'<span class="lc-chip lc-chip-uncertain">{escape(t("severity.uncertain"))}</span>'
    return f'<span class="lc-chip lc-chip-{severity}">{escape(t("severity." + severity))}</span>'


def listen_button(parts: list[str]) -> str:
    """HTML for the Listen button: read_aloud.js speaks `parts` in the current language when it is clicked."""
    return f"""
      <button type="button" class="lc-listen" data-lang="{SPEECH_TAGS[current()]}"
              data-parts="{escape(json.dumps(parts, ensure_ascii=False))}" data-listen="{escape(t('listen.button'))}"
              data-stop="{escape(t('listen.stop'))}" data-no-voice="{escape(t('listen.no_voice'))}">
        <span class="lc-listen-icon"></span><span class="lc-listen-label">{escape(t('listen.button'))}</span>
      </button>"""


def result_card(crop: str, disease: str, severity: str, confidence: float,
                description: str, uncertain: bool, spoken: list[str]) -> None:
    """The main diagnosis card: crop, disease, status chip, confidence bar and a Listen button for `spoken`."""
    accent = GREY if uncertain else SEVERITY_COLORS[severity]
    label = escape(t("result.possible" if uncertain else "result.diagnosis"))
    pct = confidence * 100
    st.html(f"""
    <div class="lc-result" style="--accent: {accent}">
      <div class="lc-result-top">
        <span class="lc-crop">{label} &middot; {escape(crop)}</span>
        {chip(severity, uncertain)}
      </div>
      <div class="lc-disease">{escape(disease)}</div>
      <p class="lc-desc">{escape(description)}</p>
      <div class="lc-conf-row"><span>{escape(t("result.confidence"))}</span><b>{pct:.1f}%</b></div>
      <div class="lc-bar"><span style="width: {pct:.1f}%"></span></div>
      {listen_button(spoken)}
    </div>
    """)


def callout(kind: str, icon: str, title: str, body: str) -> None:
    """A tinted message box. kind is 'info', 'warn' or 'error'."""
    st.html(f"""
    <div class="lc-callout lc-callout-{kind}">
      <div class="lc-icon">{icon}</div>
      <div><b>{escape(title)}</b><p>{escape(body)}</p></div>
    </div>
    """)


def helpline() -> None:
    """The free Kisan Call Centre number, as a tap-to-call card (shown to visitors who are probably in India)."""
    st.html(f"""
    <div class="lc-helpline">
      <div class="lc-icon">📞</div>
      <div><b>{escape(t("helpline.title"))}</b>
        <p>{escape(t("helpline.body"))}</p></div>
      <a href="tel:18001801551">1800-180-1551</a>
    </div>
    """)


def steps(items: list[tuple[str, str]]) -> None:
    """Numbered 'how it works' steps, shown three across on desktop."""
    cells = "".join(
        f'<div class="lc-step"><div class="lc-num">{i}</div><b>{escape(t)}</b><span>{escape(d)}</span></div>'
        for i, (t, d) in enumerate(items, start=1)
    )
    st.html(f'<div class="lc-steps">{cells}</div>')


def stat_tiles(items: list[tuple[str, str]]) -> None:
    """A row of big-number tiles, e.g. [('Test accuracy', '97.2%'), ...]."""
    cells = "".join(f'<div class="lc-stat"><span>{escape(k)}</span><b>{escape(v)}</b></div>' for k, v in items)
    st.html(f'<div class="lc-stats">{cells}</div>')


def section_label(text: str) -> None:
    st.html(f'<p class="lc-section-label">{escape(text)}</p>')


def _base_layout(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=48, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=13, color="#1E2A22"),
        showlegend=False,
        bargap=0.35,
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(autorange="reversed", ticks="", showgrid=False)
    return fig


def top_k_chart(labels: list[str], probs: list[float], uncertain: bool) -> go.Figure:
    """Horizontal bar chart of the top predictions, best first."""
    top_color = GREY if uncertain else LEAF
    fig = go.Figure(go.Bar(
        x=[p * 100 for p in probs],
        y=labels,
        orientation="h",
        marker=dict(color=[top_color] + [TRACK] * (len(probs) - 1), cornerradius=6),
        text=[f"{p:.1%}" for p in probs],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    # Labels sit above each bar (instead of on the y-axis) so long names never get clipped.
    for label in labels:
        fig.add_annotation(x=0, y=label, text=escape(label), showarrow=False, xanchor="left",
                           yanchor="bottom", yshift=13, font=dict(size=13, color="#1E2A22"))
    fig.update_xaxes(range=[0, 112])
    fig.update_yaxes(showticklabels=False)
    fig = _base_layout(fig, height=215)
    fig.update_layout(bargap=0.62, margin=dict(l=0, r=8, t=16, b=0))
    return fig


def f1_chart(names: list[str], scores: list[float]) -> go.Figure:
    """Per-class F1 bars (sorted by the caller); weakest classes are highlighted in amber."""
    colors = [AMBER if s < 0.9 else LEAF for s in scores]
    fig = go.Figure(go.Bar(
        x=scores, y=names, orientation="h",
        marker=dict(color=colors, cornerradius=4),
        text=[f"{s:.2f}" for s in scores], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: F1 %{x:.3f}<extra></extra>",
    ))
    fig.update_xaxes(range=[0, 1.05])
    fig = _base_layout(fig, height=max(300, 22 * len(names)))
    fig.update_yaxes(automargin=True)  # make room for the class names
    fig.update_layout(font=dict(size=11))
    return fig
