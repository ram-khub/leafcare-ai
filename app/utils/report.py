"""Shareable versions of a diagnosis: a message (plain or for WhatsApp) and a downloadable one-page report.

The report is a self-contained HTML page rather than a PDF: browsers render every script we
translate into (Devanagari, Bengali, Telugu, Tamil) with the fonts they already have, and the
page prints cleanly to PDF from any browser.
"""

import base64
import io
import re
from datetime import datetime
from html import escape
from urllib.parse import quote

from PIL import Image, ImageOps

from utils.i18n import current, t
from utils.ui import format_confidence

APP_URL = "https://leafcareai.streamlit.app"
HELPLINE = "1800-180-1551"


def _data_uri(image: Image.Image, size: int = 520) -> str:
    buffer = io.BytesIO()
    ImageOps.contain(image, (size, size)).save(buffer, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()


def _items(items: list[str]) -> str:
    return "".join(f"<li>{escape(item)}</li>" for item in items)


def headline(crop: str, disease: str, confidence: float, uncertain: bool) -> str:
    label = t("result.possible" if uncertain else "result.diagnosis")
    return f"{label}: {crop} · {disease} ({format_confidence(confidence)})"


def share_text(crop: str, disease: str, entry: dict, confidence: float, uncertain: bool, helpline: bool,
               whatsapp: bool = False) -> str:
    """The diagnosis and treatment as a message. `whatsapp` adds WhatsApp's *bold* and _italic_ markers."""
    bold = (lambda text: f"*{text}*") if whatsapp else str
    italic = (lambda text: f"_{text}_") if whatsapp else str
    lines = [f"🌿 {bold('LeafCare AI')}", bold(headline(crop, disease, confidence, uncertain)), "", entry["description"]]
    if not entry["is_healthy"]:
        lines += ["", bold(t("advice.organic")), *(f"• {item}" for item in entry["treatment_organic"]),
                  "", bold(t("advice.chemical")), *(f"• {item}" for item in entry["treatment_chemical"])]
    lines += ["", italic(t("advice.disclaimer"))]
    if helpline:
        lines.append(f"{t('helpline.title')}: {HELPLINE}")
    lines += ["", f"{t('share.checked_with')}: {APP_URL}"]
    return "\n".join(lines)


def whatsapp_url(crop: str, disease: str, entry: dict, confidence: float, uncertain: bool, helpline: bool) -> str:
    """A wa.me link that opens WhatsApp with the diagnosis and treatment ready to send."""
    return "https://wa.me/?text=" + quote(share_text(crop, disease, entry, confidence, uncertain, helpline,
                                                    whatsapp=True))


def file_name(class_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", class_name.lower()).strip("-")
    return f"leafcare-{slug}-{datetime.now():%Y%m%d-%H%M}.html"


def build_report(image: Image.Image, overlay: Image.Image, source: str, crop: str, disease: str, entry: dict,
                 confidence: float, uncertain: bool, helpline: bool) -> str:
    """The whole diagnosis as one HTML page with the photo, heatmap and advice embedded."""
    lang = current()
    severity = t("severity.uncertain") if uncertain else t("severity." + entry["severity"])
    if entry["is_healthy"]:
        symptoms = f"<p>{escape(t('advice.healthy_symptoms'))}</p>"
        treatment = f"<p>{escape(t('advice.healthy_treatment'))}</p>"
    else:
        symptoms = (f"<ul>{_items(entry['symptoms'])}</ul>"
                    f"<p><b>{escape(t('advice.cause'))}:</b> {escape(entry['causes'])}</p>")
        treatment = (f"<h3>{escape(t('advice.organic'))}</h3><ul>{_items(entry['treatment_organic'])}</ul>"
                     f"<h3>{escape(t('advice.chemical'))}</h3><ul>{_items(entry['treatment_chemical'])}</ul>")
    translated = f"<p>{escape(t('advice.translated'))}</p>" if lang != "en" else ""
    call = (f'<p class="help"><b>{escape(t("helpline.title"))}:</b> {HELPLINE}. {escape(t("helpline.body"))}</p>'
            if helpline else "")
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(t("report.title"))} · {escape(crop)} · {escape(disease)}</title>
<style>
  body {{ font-family: system-ui, sans-serif; color: #1E2A22; background: #FAF7F0; margin: 0; line-height: 1.5; }}
  main {{ max-width: 760px; margin: 0 auto; padding: 24px 16px 40px; }}
  header {{ display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap;
            border-bottom: 2px solid #2F6B3A; padding-bottom: 8px; }}
  header b {{ color: #2F6B3A; font-size: 1.3rem; }}
  header span, .muted {{ color: #5E6B62; font-size: 0.9rem; }}
  h1 {{ margin: 16px 0 4px; font-size: 1.7rem; }}
  h2 {{ color: #2F6B3A; font-size: 1.1rem; margin: 22px 0 6px; }}
  h3 {{ font-size: 1rem; margin: 12px 0 4px; }}
  .chip {{ display: inline-block; padding: 2px 10px; border-radius: 999px; background: #E4F0E3; font-size: 0.85rem; }}
  .images {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }}
  .images img {{ width: 100%; border-radius: 12px; }}
  .images figcaption {{ color: #5E6B62; font-size: 0.85rem; }}
  .note {{ border-top: 1px dashed #C9C2B1; margin-top: 24px; padding-top: 10px; color: #5E6B62; font-size: 0.88rem; }}
  .help {{ background: #E4F0E3; border-radius: 10px; padding: 10px 12px; }}
  @media print {{ body {{ background: #fff; }} main {{ padding: 0; }} }}
</style>
</head>
<body>
<main>
  <header><b>🌿 LeafCare AI</b><span>{escape(t("report.created", time=f"{datetime.now():%Y-%m-%d %H:%M}"))}</span></header>
  <p class="muted">{escape(t("result.possible" if uncertain else "result.diagnosis"))} · {escape(crop)}</p>
  <h1>{escape(disease)}</h1>
  <p><span class="chip">{escape(severity)}</span>
     <span class="muted">{escape(t("result.confidence"))}: <b>{escape(format_confidence(confidence))}</b></span></p>
  <p>{escape(entry["description"])}</p>
  <div class="images">
    <figure><img src="{_data_uri(image)}" alt=""><figcaption>{escape(t("home.your_photo", source=source))}</figcaption></figure>
    <figure><img src="{_data_uri(overlay)}" alt=""><figcaption>{escape(t("home.gradcam"))}</figcaption></figure>
  </div>
  <h2>{escape(t("advice.symptoms"))}</h2>{symptoms}
  <h2>{escape(t("advice.treatment"))}</h2>{treatment}
  <h2>{escape(t("advice.prevention"))}</h2><ul>{_items(entry["prevention"])}</ul>
  {call}
  <div class="note">
    <p>{escape(t("advice.source"))}: {escape(entry["source"])}</p>
    <p><b>{escape(t("advice.disclaimer"))}</b></p>
    {translated}
    <p>{escape(t("share.checked_with"))}: {APP_URL}</p>
  </div>
</main>
</body>
</html>
"""
