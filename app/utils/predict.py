"""Load the trained model and turn a leaf photo into ranked predictions."""

import json
from dataclasses import dataclass
from pathlib import Path

import keras
import numpy as np
from PIL import Image

from utils.preprocessing import image_to_model_input

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "leaf_model.keras"
CLASS_NAMES_PATH = PROJECT_ROOT / "models" / "class_names.json"
METRICS_PATH = PROJECT_ROOT / "models" / "metrics.json"
LEAF_CENTROIDS_PATH = PROJECT_ROOT / "models" / "leaf_centroids.npy"

# "Is this a leaf?" check. The model's feature vector (the avg_pool layer, just before the classifier)
# is compared with the average feature vector of each class's training leaves. Calibrated on held-out
# images: PlantVillage leaves score >= 0.50, real field photos (PlantDoc) mostly >= 0.35, and non-leaf
# photos (faces, animals, objects, a flower) <= 0.34.
EMBEDDING_LAYER = "avg_pool"
LEAF_SIMILARITY_THRESHOLD = 0.35

# scripts/make_placeholder_model.py gives its model this name so the app can
# show a "demo mode" notice. The real model from Colab has a different name.
PLACEHOLDER_MODEL_NAME = "leafcare_placeholder"


@dataclass
class Prediction:
    class_name: str                        # e.g. "Tomato___Early_blight"
    confidence: float                      # probability of the top class, 0-1
    top_k: list[tuple[str, float]]         # [(class_name, probability), ...] best first
    class_index: int                       # index of the top class (needed for Grad-CAM)
    leaf_similarity: float | None = None   # cosine similarity to the nearest class centroid; None = not checked

    @property
    def looks_like_leaf(self) -> bool:
        return self.leaf_similarity is None or self.leaf_similarity >= LEAF_SIMILARITY_THRESHOLD


def load_model(path: Path = MODEL_PATH) -> keras.Model:
    """Load a .keras model file (inference only, so no need to compile)."""
    if not path.exists():
        raise FileNotFoundError(
            f"No model found at {path}. Run `python scripts/make_placeholder_model.py` "
            "or copy your trained leaf_model.keras from Colab into models/."
        )
    return keras.models.load_model(path, compile=False)


def load_class_names(path: Path = CLASS_NAMES_PATH) -> list[str]:
    """Ordered list of class names; index i matches output neuron i of the model."""
    return json.loads(path.read_text())


def load_leaf_centroids(path: Path = LEAF_CENTROIDS_PATH) -> np.ndarray | None:
    """(num_classes, feature_dim) unit-length class centroids, or None if the file isn't there."""
    return np.load(path) if path.exists() else None


_embedding_models: dict[int, keras.Model] = {}  # cache: model id -> (features, probabilities) model


def _embedding_model(model: keras.Model) -> keras.Model:
    key = id(model)
    if key not in _embedding_models:
        _embedding_models[key] = keras.Model(model.inputs, [model.get_layer(EMBEDDING_LAYER).output, model.output])
    return _embedding_models[key]


def is_placeholder(model: keras.Model) -> bool:
    return model.name == PLACEHOLDER_MODEL_NAME


def split_class_name(class_name: str) -> tuple[str, str]:
    """'Pepper,_bell___Bacterial_spot' -> ('Pepper, bell', 'Bacterial spot')."""
    crop, _, disease = class_name.partition("___")
    return crop.replace("_", " "), disease.replace("_", " ")


def predict(model: keras.Model, image: Image.Image, class_names: list[str], top_k: int = 3,
            leaf_centroids: np.ndarray | None = None) -> Prediction:
    """Run the model on one PIL image and return the top-k classes (plus the leaf check if centroids are given)."""
    batch = image_to_model_input(image)[np.newaxis, ...]    # (1, 224, 224, 3)
    similarity = None
    if leaf_centroids is None:
        probs = model.predict_on_batch(batch)[0]            # (num_classes,)
    else:
        features, probs = _embedding_model(model).predict_on_batch(batch)
        features, probs = features[0], probs[0]
        if leaf_centroids.shape[1] != len(features):
            raise ValueError("models/leaf_centroids.npy doesn't match the model. Copy both files from the same Colab run.")
        similarity = float(np.max(leaf_centroids @ (features / np.linalg.norm(features))))
    if len(probs) != len(class_names):
        raise ValueError(
            f"Model outputs {len(probs)} classes but class_names.json lists "
            f"{len(class_names)}. Copy both files from the same Colab run."
        )

    ranked = np.argsort(probs)[::-1][:top_k]
    return Prediction(
        class_name=class_names[ranked[0]],
        confidence=float(probs[ranked[0]]),
        top_k=[(class_names[i], float(probs[i])) for i in ranked],
        class_index=int(ranked[0]),
        leaf_similarity=similarity,
    )
