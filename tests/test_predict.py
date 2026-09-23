from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from utils.predict import is_placeholder, load_leaf_centroids, predict, split_class_name

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "app" / "assets" / "sample_images"


def test_model_matches_class_list(model, class_names):
    assert len(class_names) == 38
    assert model.input_shape == (None, 224, 224, 3)
    assert model.output_shape == (None, len(class_names))


def test_prediction_output(model, class_names, leaf_image):
    result = predict(model, leaf_image, class_names, top_k=3)
    assert len(result.top_k) == 3
    probs = [p for _, p in result.top_k]
    assert probs == sorted(probs, reverse=True)
    assert all(0.0 <= p <= 1.0 for p in probs)
    assert result.class_name == result.top_k[0][0] == class_names[result.class_index]
    assert result.confidence == probs[0]


def test_split_class_name():
    assert split_class_name("Pepper,_bell___Bacterial_spot") == ("Pepper, bell", "Bacterial spot")
    assert split_class_name("Tomato___healthy") == ("Tomato", "healthy")


def test_leaf_check(model, class_names):
    centroids = load_leaf_centroids()
    if centroids is None or is_placeholder(model):
        pytest.skip("needs the trained model and models/leaf_centroids.npy")
    assert centroids.shape[0] == len(class_names)
    assert np.allclose(np.linalg.norm(centroids, axis=1), 1, atol=1e-4)

    for path in sorted(SAMPLES_DIR.iterdir()):
        result = predict(model, Image.open(path).convert("RGB"), class_names, leaf_centroids=centroids)
        assert result.looks_like_leaf, f"{path.name} rejected (similarity {result.leaf_similarity:.2f})"

    noise = Image.fromarray(np.random.default_rng(0).integers(0, 256, (224, 224, 3), dtype=np.uint8))
    assert not predict(model, noise, class_names, leaf_centroids=centroids).looks_like_leaf
