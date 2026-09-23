"""Build models/leaf_centroids.npy for the app's "is this a leaf?" check, without retraining.

For each class, averages the model's feature vectors (avg_pool layer) over up to N PlantVillage images,
then saves the unit-length class centroids. The Colab notebook writes the same file from the training
set; use this script only to rebuild it for an existing model.

Usage (from the project root), with a folder laid out like the PlantVillage repository's raw/color/:
    python scripts/build_leaf_centroids.py path/to/PlantVillage-Dataset/raw/color --per-class 25
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from utils.predict import (  # noqa: E402
    LEAF_CENTROIDS_PATH, _embedding_model, is_placeholder, load_class_names, load_model,
)
from utils.preprocessing import image_to_model_input, load_image  # noqa: E402


def folder_to_class(folder_name: str) -> str:
    """'Corn_(maize)___Common_rust_' -> 'Corn___Common_rust' (same mapping as the notebook)."""
    crop, _, disease = folder_name.partition("___")
    crop = re.sub(r"_\(.*\)$", "", crop)
    return f"{crop}___{disease.rstrip('_')}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image_dir", type=Path, help="folder with one sub-folder of images per class")
    parser.add_argument("--per-class", type=int, default=25)
    args = parser.parse_args()

    model = load_model()
    if is_placeholder(model):
        sys.exit("The placeholder model has no meaningful features. Add the trained model first.")
    class_names = load_class_names()
    folders = {folder_to_class(p.name): p for p in args.image_dir.iterdir() if p.is_dir()}
    missing = set(class_names) - set(folders)
    if missing:
        sys.exit(f"No image folder for: {sorted(missing)}")

    embedder = _embedding_model(model)
    centroids = []
    for name in class_names:
        files = sorted(p for p in folders[name].iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
        batch = np.stack([image_to_model_input(load_image(p.read_bytes())) for p in files[:args.per_class]])
        features = embedder.predict(batch, verbose=0)[0]
        features /= np.linalg.norm(features, axis=1, keepdims=True)
        centroid = features.mean(axis=0)
        centroids.append(centroid / np.linalg.norm(centroid))
        print(f"{name}: {len(batch)} images")

    np.save(LEAF_CENTROIDS_PATH, np.stack(centroids).astype(np.float32))
    print(f"Saved {LEAF_CENTROIDS_PATH} ({len(centroids)} classes)")


if __name__ == "__main__":
    main()
