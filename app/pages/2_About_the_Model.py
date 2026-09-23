"""About the Model: dataset, architecture, training, evaluation results and limitations."""

import json

import streamlit as st

from utils import ui
from utils.predict import METRICS_PATH, PROJECT_ROOT, split_class_name

FIGURES = PROJECT_ROOT / "reports" / "figures"

ui.page_header(
    "How it works",
    "About the model",
    "LeafCare AI uses transfer learning: a network pre-trained on millions of everyday photos "
    "is fine-tuned to recognise 38 leaf conditions across 14 crops.",
)

# ---------------------------------------------------------------- results
st.subheader("Results on the held-out test set")
if METRICS_PATH.exists():
    metrics = json.loads(METRICS_PATH.read_text())
    ui.stat_tiles([
        ("Test accuracy", f"{metrics['test_accuracy']:.1%}"),
        ("Macro F1", f"{metrics['macro_f1']:.3f}"),
        ("Test images", f"{metrics['num_test_images']:,}"),
        ("Classes", str(metrics["num_classes"])),
    ])
    st.caption(f"Trained with TensorFlow {metrics.get('tf_version', '?')}.")
else:
    metrics = None
    ui.callout("info", "📊", "No metrics yet",
               "Train the model with notebooks/train_model.ipynb in Google Colab, then copy "
               "models/metrics.json and reports/figures/ into this project to see the results here.")

curves, confusion = FIGURES / "training_curves.png", FIGURES / "confusion_matrix.png"
if curves.exists():
    with st.container(key="card_curves"):
        ui.section_label("Training curves (accuracy and loss)")
        st.image(str(curves), width="stretch")
if confusion.exists():
    with st.container(key="card_confusion"):
        ui.section_label("Normalised confusion matrix")
        st.image(str(confusion), width="stretch")
        st.caption("Each row is the true class; a bright diagonal means most images are classified correctly.")
if metrics:
    with st.container(key="card_f1"):
        ui.section_label("F1 score per class (amber = below 0.90)")
        ranked = sorted(metrics["per_class_f1"].items(), key=lambda item: item[1])
        names = [" · ".join(split_class_name(name)) for name, _ in ranked]
        st.plotly_chart(ui.f1_chart(names, [score for _, score in ranked]),
                        config={"displayModeBar": False}, theme=None)

# ---------------------------------------------------------------- method
st.write("")
st.subheader("Dataset")
st.markdown(
    "- **PlantVillage**: about 54,000 labelled leaf images, 38 classes across 14 crops, "
    "including a *healthy* class for 12 of the crops.\n"
    "- Split **80 / 10 / 10** into train / validation / test sets, stratified by class so every "
    "class is represented in the same proportion (random seed 42).\n"
    "- Images are resized to 224 × 224 pixels, using the same function in training and in this app."
)

st.subheader("Architecture")
st.html("""
<div class="lc-flow">
  <span>Leaf photo 224×224×3</span><i>→</i>
  <span>EfficientNetB0 (ImageNet weights)</span><i>→</i>
  <span>Global average pooling</span><i>→</i>
  <span>Dropout 0.3</span><i>→</i>
  <span>Dense 38 · softmax</span>
</div>
""")
st.markdown(
    "EfficientNetB0 is a compact convolutional network (about 4 million parameters) that is fast "
    "enough for a web app. Its final convolutional layer, `top_conv`, is also what Grad-CAM uses to "
    "draw the heatmap on the Diagnose page."
)

st.subheader("Training approach")
st.markdown(
    "1. **Data augmentation** (random flips, rotation, zoom, brightness, contrast and slight "
    "cropping) so the model copes better with real-world photos.\n"
    "2. **Phase 1, feature extraction:** the pre-trained backbone is frozen and only the new "
    "classification head is trained (about 5 epochs, Adam, learning rate 1e-3).\n"
    "3. **Phase 2, fine-tuning:** the top ~30% of the backbone is unfrozen (BatchNorm layers stay "
    "frozen) and trained with a much smaller learning rate (1e-5, about 10 epochs).\n"
    "4. **Early stopping** (patience 3) keeps the weights from the best validation epoch."
)

# ---------------------------------------------------------------- limitations
st.subheader("Limitations")
st.html("""
<div class="lc-card">
  <ul>
    <li><b>Lab-style training photos.</b> PlantVillage leaves were photographed one at a time on
        plain backgrounds. Accuracy on real field photos (cluttered backgrounds, several leaves,
        shadows, blur) is noticeably lower than the test score above.</li>
    <li><b>Only 38 known classes.</b> The model can only recognise the 14 crops and 38 conditions it
        was trained on. A leaf from any other plant or disease will still be forced into one of them,
        which is why low-confidence results show a warning.</li>
    <li><b>Not a substitute for an expert.</b> Advice is general and informational. Always confirm
        with an agronomist or local agricultural officer before applying treatments.</li>
  </ul>
</div>
""")
