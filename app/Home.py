"""LeafCare AI: entry point (shared setup + navigation) and the Diagnose page.

Run from the project root:
    streamlit run app/Home.py
"""

import hashlib
import io
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
from PIL import Image, ImageOps

from utils import ui
from utils.gradcam import make_gradcam_heatmap, overlay_heatmap
from utils.predict import (
    PROJECT_ROOT, Prediction, is_placeholder, load_class_names, load_leaf_centroids, load_model, predict,
    split_class_name,
)
from utils.preprocessing import ImageError, image_to_model_input, load_image

APP_DIR = Path(__file__).parent
SAMPLES_DIR = APP_DIR / "assets" / "sample_images"
DISEASES_PATH = PROJECT_ROOT / "data" / "diseases.json"

CONFIDENCE_THRESHOLD = 0.60  # below this we ask for a better photo instead of trusting the result
DISCLAIMER = "Informational only — consult a local agricultural officer before applying any chemicals."
UPLOAD, CAMERA, SAMPLE = ":material/upload: Upload", ":material/photo_camera: Camera", ":material/eco: Try a sample"


# ---------------------------------------------------------------- cached resources

@st.cache_resource(show_spinner="Loading the AI model…")
def get_model():
    return load_model()


@st.cache_resource
def get_class_names() -> list[str]:
    return load_class_names()


@st.cache_resource
def get_leaf_centroids():
    return None if is_placeholder(get_model()) else load_leaf_centroids()


@st.cache_data
def get_knowledge_base() -> dict:
    return json.loads(DISEASES_PATH.read_text())


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
        st.caption("No sample images found in app/assets/sample_images/.")
        return None
    selected = st.session_state.get("sample")
    columns = st.container(key="samples").columns(len(samples))
    for column, path in zip(columns, samples):
        with column:
            st.image(square_thumbnail(str(path)), caption=sample_caption(path), width="stretch")
            is_selected = path.name == selected
            if st.button("Selected" if is_selected else "Use this", key=f"sample_{path.name}",
                         type="primary" if is_selected else "secondary", width="stretch"):
                st.session_state.sample = path.name
                st.rerun()
    if selected and (SAMPLES_DIR / selected).exists():
        return (SAMPLES_DIR / selected).read_bytes(), sample_caption(SAMPLES_DIR / selected)
    return None


def get_input_image() -> tuple[bytes, str] | None:
    """Show the three input options and return (image bytes, source label) if one was provided."""
    mode = st.segmented_control(
        "How would you like to add a photo?", [UPLOAD, CAMERA, SAMPLE],
        default=UPLOAD, required=True, key="input_mode", label_visibility="collapsed",
    )
    if mode == UPLOAD:
        file = st.file_uploader(
            "Upload a leaf photo", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed",
            help="A close-up of a single leaf on a plain background works best.",
        )
        return (file.getvalue(), file.name) if file else None
    if mode == CAMERA:
        shot = st.camera_input("Take a photo of a single leaf", label_visibility="collapsed")
        return (shot.getvalue(), "Camera photo") if shot else None
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
    crop, disease = display_names(prediction.class_name)
    history.insert(0, {
        "id": digest,
        "thumbnail": buffer.getvalue(),
        "crop": crop,
        "disease": disease,
        "severity": get_knowledge_base().get(prediction.class_name, {}).get("severity", "moderate"),
        "confidence": prediction.confidence,
        "uncertain": uncertain,
        "time": datetime.now().strftime("%H:%M:%S"),
    })


def bullet_list(items: list[str]) -> None:
    st.markdown("\n".join(f"- {item}" for item in items))


def show_advice(entry: dict) -> None:
    """Symptoms / Treatment / Prevention tabs plus source and disclaimer."""
    symptoms_tab, treatment_tab, prevention_tab = st.tabs(
        [":material/search: Symptoms", ":material/medication: Treatment", ":material/shield: Prevention"]
    )
    with symptoms_tab:
        if entry["is_healthy"]:
            st.markdown("No disease symptoms detected. Healthy leaves are evenly coloured, "
                        "without spots, mould, holes or curling.")
        else:
            bullet_list(entry["symptoms"])
            st.markdown(f"**Cause:** {entry['causes']}")
    with treatment_tab:
        if entry["is_healthy"]:
            st.markdown("No treatment needed. Keep monitoring the plant regularly.")
        else:
            organic, chemical = st.columns(2, gap="large")
            with organic:
                st.markdown("##### :material/eco: Organic & cultural")
                bullet_list(entry["treatment_organic"])
            with chemical:
                st.markdown("##### :material/science: Chemical")
                bullet_list(entry["treatment_chemical"])
    with prevention_tab:
        bullet_list(entry["prevention"])

    domain = urlparse(entry["source"]).netloc.removeprefix("www.")
    st.html(f"""
    <div class="lc-disclaimer">
      Source: <a href="{entry['source']}" target="_blank" rel="noopener">{domain}</a><br>
      <b>{DISCLAIMER}</b>
    </div>
    """)


# ---------------------------------------------------------------- the Diagnose page

def diagnose_page() -> None:
    ui.hero("LeafCare AI", "Snap a leaf, spot crop disease early, and protect your harvest.")

    try:
        model = get_model()
    except FileNotFoundError as err:
        ui.callout("error", "⚠️", "Model not found", str(err))
        return
    if is_placeholder(model):
        ui.callout("info", "🧪", "Demo mode",
                   "The app is running an untrained placeholder model, so results are random. "
                   "Copy leaf_model.keras from the Colab notebook into models/ for real diagnoses.")

    with st.container(key="card_input"):
        ui.section_label("Step 1 · Add a leaf photo")
        picked = get_input_image()

    if picked is None:
        st.write("")
        ui.steps([
            ("Add a photo", "Upload, snap with your camera, or try one of the samples."),
            ("AI analyses it", "A deep-learning model checks the leaf against 38 crop conditions."),
            ("Get advice", "See the likely disease, where the model looked, and what to do next."),
        ])
        ui.callout("info", "💡", "Tips for a good photo",
                   "Photograph one leaf, fill the frame, use natural light, and place it on a plain background.")
        return

    image_bytes, source = picked
    try:
        image = load_image(image_bytes)
        with st.spinner("Analysing leaf…"):
            prediction, overlay = analyse(image_bytes)
    except ImageError as err:
        ui.callout("error", "⚠️", "We couldn't use that image", str(err))
        return
    except ValueError as err:  # e.g. model and class list don't match
        ui.callout("error", "⚠️", "Model problem", str(err))
        return

    digest = hashlib.md5(image_bytes).hexdigest()
    if not prediction.looks_like_leaf and st.session_state.get("leaf_override") != digest:
        st.write("")
        ui.callout("warn", "🍃", "This doesn't look like a leaf",
                   "LeafCare AI only recognises leaves of 14 crops, so other photos give meaningless results. "
                   "Please use a close-up of a single leaf. If this is a leaf, you can still run the diagnosis.")
        if st.button("It's a leaf, analyse anyway", icon=":material/eco:"):
            st.session_state.leaf_override = digest
            st.rerun()
        return

    uncertain = prediction.confidence < CONFIDENCE_THRESHOLD
    record_scan(image, image_bytes, prediction, uncertain)
    entry = get_knowledge_base()[prediction.class_name]
    crop, disease = display_names(prediction.class_name)

    st.write("")
    ui.section_label("Step 2 · Results")
    if uncertain:
        ui.callout("warn", "📸", "We're not sure about this one",
                   f"The model is only {prediction.confidence:.0%} confident, so treat this result as a guess. "
                   "Please try a clearer, closer photo of a single leaf on a plain background, in good light.")

    result_col, chart_col = st.columns([1.35, 1], gap="medium")
    with result_col:
        ui.result_card(crop, disease, entry["severity"], prediction.confidence, entry["description"], uncertain)
    with chart_col, st.container(key="card_top3"):
        ui.section_label("Top 3 predictions")
        labels = [" · ".join(display_names(name)) for name, _ in prediction.top_k]
        st.plotly_chart(ui.top_k_chart(labels, [p for _, p in prediction.top_k], uncertain),
                        config={"displayModeBar": False}, theme=None)

    st.write("")
    with st.container(key="card_images"):
        original_col, heatmap_col = st.columns(2, gap="medium")
        with original_col:
            ui.section_label(f"Your photo · {source}")
            st.image(image, width="stretch")
        with heatmap_col:
            ui.section_label("Where the model looked (Grad-CAM)")
            st.image(overlay, width="stretch")
        st.html('<p class="lc-caption">Red and yellow areas influenced the prediction most; '
                'blue areas mattered least. If the hot spots sit on the background rather than the leaf, '
                'try a new photo.</p>')

    st.write("")
    if uncertain:
        with st.expander(f"Information about the closest match: {crop} · {disease} (unconfirmed)"):
            show_advice(entry)
    else:
        with st.container(key="card_advice"):
            ui.section_label("What to do next")
            show_advice(entry)


# ---------------------------------------------------------------- app frame + navigation

st.set_page_config(page_title="LeafCare AI", page_icon="🌿", layout="wide")
ui.inject_css()
st.logo(str(ui.LOGO_PATH), size="large")
st.session_state.setdefault("history", [])

navigation = st.navigation(
    [
        st.Page(diagnose_page, title="Diagnose", icon=":material/eco:", default=True),
        st.Page("pages/1_Scan_History.py", title="Scan History", icon=":material/history:"),
        st.Page("pages/2_About_the_Model.py", title="About the Model", icon=":material/neurology:"),
        st.Page("pages/3_SDG_Impact.py", title="SDG Impact", icon=":material/public:"),
    ],
    position="top",
)
navigation.run()
