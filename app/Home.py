"""LeafCare AI: entry point (shared setup + navigation) and the Diagnose page.

Run from the project root:
    streamlit run app/Home.py
"""

import hashlib
import io
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
from PIL import Image, ImageOps

from utils import i18n, report, ui
from utils.gradcam import make_gradcam_heatmap, overlay_heatmap
from utils.i18n import t
from utils.predict import (
    PROJECT_ROOT, Prediction, is_placeholder, load_class_names, load_leaf_centroids, load_model, predict,
    split_class_name,
)
from utils.preprocessing import ImageError, image_to_model_input, load_image

APP_DIR = Path(__file__).parent
SAMPLES_DIR = APP_DIR / "assets" / "sample_images"

CONFIDENCE_THRESHOLD = 0.60  # below this we ask for a better photo instead of trusting the result
# Values of the input-mode control (stable across languages); labels come from INPUT_LABELS.
UPLOAD, CAMERA, SAMPLE = ":material/upload: Upload", ":material/photo_camera: Camera", ":material/eco: Try a sample"
INPUT_LABELS = {UPLOAD: (":material/upload:", "input.upload"), CAMERA: (":material/photo_camera:", "input.camera"),
                SAMPLE: (":material/eco:", "input.sample")}


# ---------------------------------------------------------------- cached resources

@st.cache_resource(show_spinner=False)  # the translated spinner is in diagnose_page()
def get_model():
    return load_model()


@st.cache_resource
def get_class_names() -> list[str]:
    return load_class_names()


@st.cache_resource
def get_leaf_centroids():
    return None if is_placeholder(get_model()) else load_leaf_centroids()


def get_knowledge_base() -> dict:
    """The disease knowledge base in the visitor's language."""
    return i18n.knowledge_base(i18n.current())


@st.cache_data(max_entries=50, show_spinner=False)
def analyse(image_bytes: bytes) -> tuple[Prediction, Image.Image]:
    """Prediction + Grad-CAM overlay. Cached so re-runs (e.g. switching tabs) are instant."""
    image = load_image(image_bytes)
    model = get_model()
    prediction = predict(model, image, get_class_names(), leaf_centroids=get_leaf_centroids())
    heatmap = make_gradcam_heatmap(model, image_to_model_input(image), prediction.class_index)
    return prediction, overlay_heatmap(image, heatmap)


@st.cache_data
def square_thumbnail(path: str, size: int = 240) -> Image.Image:
    return ImageOps.fit(Image.open(path).convert("RGB"), (size, size))


# ---------------------------------------------------------------- helpers

def display_names(class_name: str) -> tuple[str, str]:
    """(crop, disease) as written in the knowledge base, falling back to the raw class name."""
    entry = get_knowledge_base().get(class_name)
    return (entry["crop"], entry["disease"]) if entry else split_class_name(class_name)


def sample_caption(path: Path) -> str:
    if path.stem in get_class_names():
        crop, disease = display_names(path.stem)
        return f"{crop} · {disease}"
    return path.stem.replace("_", " ").capitalize()


def pick_sample() -> tuple[bytes, str] | None:
    samples = sorted(p for p in SAMPLES_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})[:6]
    if not samples:
        st.caption(t("input.no_samples"))
        return None
    selected = st.session_state.get("sample")
    columns = st.container(key="samples").columns(len(samples))
    for column, path in zip(columns, samples):
        with column:
            st.image(square_thumbnail(str(path)), caption=sample_caption(path), width="stretch")
            is_selected = path.name == selected
            if st.button(t("input.selected") if is_selected else t("input.use_this"), key=f"sample_{path.name}",
                         type="primary" if is_selected else "secondary", width="stretch"):
                st.session_state.sample = path.name
                st.rerun()
    if selected and (SAMPLES_DIR / selected).exists():
        return (SAMPLES_DIR / selected).read_bytes(), sample_caption(SAMPLES_DIR / selected)
    return None


def get_input_image() -> tuple[bytes, str] | None:
    """Show the three input options and return (image bytes, source label) if one was provided."""
    round_ = st.session_state.get("input_round", 0)  # bumped by "Scan another leaf" to empty the photo inputs
    mode = st.segmented_control(
        t("input.mode_label"), [UPLOAD, CAMERA, SAMPLE],
        format_func=lambda mode: f"{INPUT_LABELS[mode][0]} {t(INPUT_LABELS[mode][1])}",
        default=UPLOAD, required=True, key="input_mode", label_visibility="collapsed",
    )
    if mode == UPLOAD:
        file = st.file_uploader(
            t("input.upload_label"), type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed",
            help=t("input.upload_help"), key=f"upload_{round_}",  # a key keeps the file when the language changes
        )
        return (file.getvalue(), file.name) if file else None
    if mode == CAMERA:
        shot = st.camera_input(t("input.camera_label"), label_visibility="collapsed", key=f"camera_{round_}")
        return (shot.getvalue(), t("input.camera_source")) if shot else None
    return pick_sample()


def record_scan(image: Image.Image, image_bytes: bytes, prediction: Prediction, uncertain: bool) -> None:
    """Add this scan to the session's history (once per distinct image)."""
    digest = hashlib.md5(image_bytes).hexdigest()
    history = st.session_state.history
    if any(scan["id"] == digest for scan in history):
        return
    thumb = ImageOps.fit(image, (160, 160))
    buffer = io.BytesIO()
    thumb.save(buffer, format="JPEG", quality=85)
    history.insert(0, {
        "id": digest,
        "thumbnail": buffer.getvalue(),
        "class_name": prediction.class_name,  # names are looked up at display time, in the current language
        "severity": get_knowledge_base().get(prediction.class_name, {}).get("severity", "moderate"),
        "confidence": prediction.confidence,
        "uncertain": uncertain,
        "time": datetime.now().strftime("%H:%M:%S"),
    })


def bullet_list(items: list[str]) -> None:
    st.markdown("\n".join(f"- {item}" for item in items))


def new_scan_button() -> None:
    """Clear the current photo so the next one can be added straight away."""
    if st.button(t("home.new_scan"), icon=":material/restart_alt:", type="primary"):
        st.session_state.input_round = st.session_state.get("input_round", 0) + 1  # new keys: empty inputs
        for key in ("sample", "leaf_override"):
            st.session_state.pop(key, None)
        st.rerun()


def spoken_summary(entry: dict, crop: str, disease: str, uncertain: bool) -> list[str]:
    """What the Listen button reads out: the diagnosis, what it means and what to do."""
    parts = [t("uncertain.title")] if uncertain else []
    parts += [f"{t('result.possible' if uncertain else 'result.diagnosis')}: {crop}, {disease}.", entry["description"]]
    if entry["is_healthy"]:
        parts.append(t("advice.healthy_treatment"))
    else:
        parts += [f"{t('advice.organic')}:", *entry["treatment_organic"],
                  f"{t('advice.chemical')}:", *entry["treatment_chemical"]]
    return parts + [t("advice.disclaimer")]


def show_advice(entry: dict) -> None:
    """Symptoms / Treatment / Prevention tabs plus source and disclaimer."""
    symptoms_tab, treatment_tab, prevention_tab = st.tabs(
        [f":material/search: {t('advice.symptoms')}", f":material/medication: {t('advice.treatment')}",
         f":material/shield: {t('advice.prevention')}"]
    )
    with symptoms_tab:
        if entry["is_healthy"]:
            st.markdown(t("advice.healthy_symptoms"))
        else:
            bullet_list(entry["symptoms"])
            st.markdown(f"**{t('advice.cause')}:** {entry['causes']}")
    with treatment_tab:
        if entry["is_healthy"]:
            st.markdown(t("advice.healthy_treatment"))
        else:
            organic, chemical = st.columns(2, gap="large")
            with organic:
                st.markdown(f"##### :material/eco: {t('advice.organic')}")
                bullet_list(entry["treatment_organic"])
            with chemical:
                st.markdown(f"##### :material/science: {t('advice.chemical')}")
                bullet_list(entry["treatment_chemical"])
    with prevention_tab:
        bullet_list(entry["prevention"])

    domain = urlparse(entry["source"]).netloc.removeprefix("www.")
    translated = f"<br>{escape(t('advice.translated'))}" if i18n.current() != "en" else ""
    st.html(f"""
    <div class="lc-disclaimer">
      {escape(t("advice.source"))}: <a href="{entry['source']}" target="_blank" rel="noopener">{domain}</a><br>
      <b>{escape(t("advice.disclaimer"))}</b>{translated}
    </div>
    """)
    if i18n.likely_in_india():
        ui.helpline()


def share_buttons(image: Image.Image, overlay: Image.Image, source: str, prediction: Prediction,
                  entry: dict, crop: str, disease: str, uncertain: bool) -> None:
    """Send the result on WhatsApp or save it as a report."""
    helpline = i18n.likely_in_india()
    ui.section_label(t("share.title"))
    with st.container(horizontal=True, key="share"):
        st.link_button(t("share.whatsapp"), icon=":material/share:", url=report.whatsapp_url(
            crop, disease, entry, prediction.confidence, uncertain, helpline))
        st.html(ui.copy_button(report.share_text(crop, disease, entry, prediction.confidence, uncertain, helpline)),
                width="content")
        st.download_button(
            t("share.download"), icon=":material/download:", help=t("share.download_help"), on_click="ignore",
            data=report.build_report(image, overlay, source, crop, disease, entry, prediction.confidence,
                                     uncertain, helpline),
            file_name=report.file_name(prediction.class_name), mime="text/html",
        )


# ---------------------------------------------------------------- the Diagnose page

def diagnose_page() -> None:
    ui.hero("LeafCare AI", t("hero.tagline"))

    try:
        with st.spinner(t("home.loading_model")):
            model = get_model()
    except FileNotFoundError as err:
        ui.callout("error", "⚠️", t("home.model_missing"), str(err))
        return
    if is_placeholder(model):
        ui.callout("info", "🧪", t("home.demo_title"), t("home.demo_body"))

    with st.container(key="card_input"):
        ui.section_label(t("home.step1"))
        picked = get_input_image()

    if picked is None:
        st.write("")
        ui.steps([
            (t("steps.add_title"), t("steps.add_body")),
            (t("steps.analyse_title"), t("steps.analyse_body")),
            (t("steps.advice_title"), t("steps.advice_body")),
        ])
        ui.callout("info", "💡", t("tips.title"), t("tips.body"))
        return

    image_bytes, source = picked
    try:
        image = load_image(image_bytes)
        with st.spinner(t("home.analysing")):
            prediction, overlay = analyse(image_bytes)
    except ImageError as err:
        ui.callout("error", "⚠️", t("error.bad_image"), t(f"error.{err.reason}", **err.values))
        return
    except ValueError as err:  # e.g. model and class list don't match
        ui.callout("error", "⚠️", t("error.model"), str(err))
        return

    digest = hashlib.md5(image_bytes).hexdigest()
    if not prediction.looks_like_leaf and st.session_state.get("leaf_override") != digest:
        st.write("")
        ui.callout("warn", "🍃", t("leafcheck.title"), t("leafcheck.body"))
        if st.button(t("leafcheck.button"), icon=":material/eco:"):
            st.session_state.leaf_override = digest
            st.rerun()
        return

    uncertain = prediction.confidence < CONFIDENCE_THRESHOLD
    record_scan(image, image_bytes, prediction, uncertain)
    entry = get_knowledge_base()[prediction.class_name]
    crop, disease = display_names(prediction.class_name)

    st.write("")
    ui.section_label(t("home.step2"))
    if uncertain:
        ui.callout("warn", "📸", t("uncertain.title"), t("uncertain.body", confidence=f"{prediction.confidence:.0%}"))

    result_col, chart_col = st.columns([1.35, 1], gap="medium")
    with result_col:
        ui.result_card(crop, disease, entry["severity"], prediction.confidence, entry["description"], uncertain,
                       spoken_summary(entry, crop, disease, uncertain))
    with chart_col, st.container(key="card_top3"):
        ui.section_label(t("home.top3"))
        labels = [" · ".join(display_names(name)) for name, _ in prediction.top_k]
        st.plotly_chart(ui.top_k_chart(labels, [p for _, p in prediction.top_k], uncertain),
                        config={"displayModeBar": False}, theme=None)

    st.write("")
    with st.container(key="card_images"):
        original_col, heatmap_col = st.columns(2, gap="medium")
        with original_col:
            ui.section_label(t("home.your_photo", source=source))
            st.image(image, width="stretch")
        with heatmap_col:
            ui.section_label(t("home.gradcam"))
            st.image(overlay, width="stretch")
        st.html(f'<p class="lc-caption">{escape(t("home.gradcam_caption"))}</p>')

    st.write("")
    if uncertain:
        with st.expander(t("home.closest_match", name=f"{crop} · {disease}")):
            show_advice(entry)
    else:
        with st.container(key="card_advice"):
            ui.section_label(t("home.next"))
            show_advice(entry)

    st.write("")
    share_buttons(image, overlay, source, prediction, entry, crop, disease, uncertain)
    st.write("")
    new_scan_button()


# ---------------------------------------------------------------- app frame + navigation

st.set_page_config(page_title="LeafCare AI", page_icon="🌿", layout="wide")
ui.inject_css()
i18n.language_picker()  # first: it settles the language everything below is shown in
ui.page_scripts()
st.logo(str(ui.LOGO_PATH), size="large")
st.session_state.setdefault("history", [])

navigation = st.navigation(
    [
        st.Page(diagnose_page, title=t("nav.diagnose"), icon=":material/eco:", default=True),
        st.Page("views/1_Scan_History.py", title=t("nav.history"), icon=":material/history:"),
        st.Page("views/2_About_the_Model.py", title=t("nav.about"), icon=":material/neurology:"),
        st.Page("views/3_SDG_Impact.py", title=t("nav.sdg"), icon=":material/public:"),
        st.Page("views/4_Feedback.py", title=t("nav.feedback"), icon=":material/feedback:"),
    ],
    position="top",
)
navigation.run()
