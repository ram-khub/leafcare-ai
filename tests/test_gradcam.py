import numpy as np

from utils.gradcam import make_gradcam_heatmap, overlay_heatmap
from utils.preprocessing import image_to_model_input


def test_heatmap_is_2d_and_normalised(model, leaf_image):
    heatmap = make_gradcam_heatmap(model, image_to_model_input(leaf_image), class_index=0)
    assert heatmap.ndim == 2
    assert heatmap.min() >= 0.0 and heatmap.max() <= 1.0


def test_overlay_keeps_original_size(leaf_image):
    heatmap = np.random.default_rng(0).random((7, 7))
    overlay = overlay_heatmap(leaf_image, heatmap)
    assert overlay.size == leaf_image.size
    assert overlay.mode == "RGB"


def test_heatmap_uses_the_score_before_softmax(model, leaf_image):
    """The raw scores rebuilt from the final Dense layer must match the model's own output after softmax."""
    import tensorflow as tf

    from utils.gradcam import LAST_CONV_LAYER, _gradcam_model

    batch = image_to_model_input(leaf_image)[np.newaxis, ...]
    _, features = _gradcam_model(model, LAST_CONV_LAYER)(batch, training=False)
    head = model.layers[-1]
    logits = tf.matmul(features, head.kernel) + head.bias
    np.testing.assert_allclose(tf.nn.softmax(logits).numpy(), model(batch, training=False).numpy(), atol=1e-5)
