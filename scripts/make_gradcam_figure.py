"""Redraw reports/figures/gradcam_examples.png from the trained model, without re-running training.

The notebook draws the same figure from test-set images while it still has the dataset in Colab
(section 11). This script is for afterwards: it uses models/leaf_model.keras and the photos in
app/assets/sample_images/, so it needs nothing but the repo and runs in seconds.

Run from the project root:  python scripts/make_gradcam_figure.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from utils.gradcam import make_gradcam_heatmap, overlay_heatmap  # noqa: E402
from utils.predict import is_placeholder, load_class_names, load_model, predict, split_class_name  # noqa: E402
from utils.preprocessing import image_to_model_input, load_image  # noqa: E402
from utils.ui import format_confidence  # noqa: E402

SAMPLES_DIR = PROJECT_ROOT / "app" / "assets" / "sample_images"
OUTPUT = PROJECT_ROOT / "reports" / "figures" / "gradcam_examples.png"


def main() -> None:
    model = load_model()
    if is_placeholder(model):
        raise SystemExit("models/leaf_model.keras is the untrained placeholder: copy the real model from Colab first.")
    class_names = load_class_names()

    photos = sorted(p for p in SAMPLES_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if not photos:
        raise SystemExit(f"No sample photos in {SAMPLES_DIR}.")

    rows = len(photos)
    figure, axes = plt.subplots(rows, 2, figsize=(7, 3.5 * rows), squeeze=False)
    for (photo_axis, heatmap_axis), path in zip(axes, photos):
        image = load_image(path.read_bytes())
        prediction = predict(model, image, class_names)
        heatmap = make_gradcam_heatmap(model, image_to_model_input(image), prediction.class_index)
        crop, disease = split_class_name(prediction.class_name)
        title = f"{crop} · {disease} ({format_confidence(prediction.confidence)})"
        for axis, panel, label in ((photo_axis, image, "photo"),
                                   (heatmap_axis, overlay_heatmap(image, heatmap), "Grad-CAM")):
            axis.imshow(panel)
            axis.set_title(f"{title}\n{label}", fontsize=8)
            axis.axis("off")

    figure.suptitle("Grad-CAM on app/assets/sample_images (red = drove the prediction)", fontsize=11)
    figure.tight_layout(rect=(0, 0, 1, 0.985))  # leave room for the suptitle above the first row
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT, dpi=110, bbox_inches="tight")
    print(f"Wrote {OUTPUT.relative_to(PROJECT_ROOT)} ({len(photos)} photos)")


if __name__ == "__main__":
    main()
