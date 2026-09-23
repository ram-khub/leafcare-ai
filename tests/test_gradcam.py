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
