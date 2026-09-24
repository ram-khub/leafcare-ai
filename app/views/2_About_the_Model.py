"""About the Model: dataset, architecture, training, evaluation results and limitations."""

import json

import streamlit as st

from utils import i18n, ui
from utils.i18n import t
from utils.predict import METRICS_PATH, PROJECT_ROOT, split_class_name

FIGURES = PROJECT_ROOT / "reports" / "figures"

ui.page_header(t("about.eyebrow"), t("about.title"), t("about.subtitle"))

# ---------------------------------------------------------------- results
st.subheader(t("about.results"))
if METRICS_PATH.exists():
    metrics = json.loads(METRICS_PATH.read_text())
    ui.stat_tiles([
        (t("about.accuracy"), f"{metrics['test_accuracy']:.1%}"),
        (t("about.macro_f1"), f"{metrics['macro_f1']:.3f}"),
        (t("about.test_images"), f"{metrics['num_test_images']:,}"),
        (t("about.classes"), str(metrics["num_classes"])),
    ])
    st.caption(t("about.trained_with", version=metrics.get("tf_version", "?")))
else:
    metrics = None
    ui.callout("info", "📊", t("about.no_metrics_title"), t("about.no_metrics_body"))

curves, confusion = FIGURES / "training_curves.png", FIGURES / "confusion_matrix.png"
if curves.exists():
    with st.container(key="card_curves"):
        ui.section_label(t("about.curves"))
        st.image(str(curves), width="stretch")
if confusion.exists():
    with st.container(key="card_confusion"):
        ui.section_label(t("about.confusion"))
        st.image(str(confusion), width="stretch")
        st.caption(t("about.confusion_caption"))
if metrics:
    with st.container(key="card_f1"):
        ui.section_label(t("about.f1"))
        ranked = sorted(metrics["per_class_f1"].items(), key=lambda item: item[1])
        knowledge_base = i18n.knowledge_base(i18n.current())
        names = [f"{knowledge_base[name]['crop']} · {knowledge_base[name]['disease']}" if name in knowledge_base
                 else " · ".join(split_class_name(name)) for name, _ in ranked]
        st.plotly_chart(ui.f1_chart(names, [score for _, score in ranked]),
                        config={"displayModeBar": False}, theme=None)

# ---------------------------------------------------------------- method
st.write("")
st.subheader(t("about.dataset"))
st.markdown(t("about.dataset_body"))

st.subheader(t("about.architecture"))
st.html(f"""
<div class="lc-flow">
  <span>{t("about.flow_input")}</span><i>→</i>
  <span>{t("about.flow_backbone")}</span><i>→</i>
  <span>{t("about.flow_pooling")}</span><i>→</i>
  <span>Dropout 0.3</span><i>→</i>
  <span>Dense 38 · softmax</span>
</div>
""")
st.markdown(t("about.architecture_body"))

st.subheader(t("about.training"))
st.markdown(t("about.training_body"))

# ---------------------------------------------------------------- limitations
st.subheader(t("about.limitations"))
items = "".join(f"<li><b>{t(f'about.limit_{name}_title')}</b> {t(f'about.limit_{name}_body')}</li>"
                for name in ("lab", "classes", "expert"))
st.html(f'<div class="lc-card"><ul>{items}</ul></div>')
