"""Grad-CAM: highlight the parts of the leaf that drove the model's decision.

How it works (Selvaraju et al., 2017):
1. Take the feature maps of the last convolutional layer ("top_conv" in EfficientNetB0).
2. Compute the gradient of the predicted class score with respect to those maps. The score is the
   raw one from before the softmax, as in the paper. The softmax probability of a confident
   prediction barely moves, so its gradient mostly shows what separates the class from the
   runner-up (for Tomato late blight: tomato leaf shape vs potato), not the disease itself.
3. Average each map's gradient to get its importance weight, then take the
   weighted sum of the maps. Keep positive values only and scale to 0-1.
"""

import cv2
import keras
import numpy as np
import tensorflow as tf
from PIL import Image

LAST_CONV_LAYER = "top_conv"

_gradcam_models: dict[tuple[int, str], keras.Model] = {}  # cache: (model id, layer) -> gradient model


def _gradcam_model(model: keras.Model, layer_name: str) -> keras.Model:
    """A model that returns (last conv feature maps, the input of the final Dense layer) in one pass."""
    key = (id(model), layer_name)
    if key not in _gradcam_models:
        _gradcam_models[key] = keras.Model(
            inputs=model.input,  # a single tensor, like the model itself (a list here makes Keras warn)
            outputs=[model.get_layer(layer_name).output, model.layers[-1].input],
        )
    return _gradcam_models[key]


def make_gradcam_heatmap(
    model: keras.Model, model_input: np.ndarray, class_index: int, layer_name: str = LAST_CONV_LAYER
) -> np.ndarray:
    """Return a 2-D heatmap (feature-map resolution, e.g. 7x7) with values in [0, 1].

    `model_input` is one preprocessed image of shape (224, 224, 3).
    """
    grad_model = _gradcam_model(model, layer_name)
    head = model.layers[-1]  # Dense(num_classes, softmax)
    batch = tf.convert_to_tensor(model_input[np.newaxis, ...])

    with tf.GradientTape() as tape:
        conv_maps, features = grad_model(batch, training=False)
        logits = tf.matmul(features, head.kernel) + head.bias  # the final layer without its softmax
        class_score = logits[:, class_index]

    grads = tape.gradient(class_score, conv_maps)            # (1, h, w, channels)
    weights = tf.reduce_mean(grads, axis=(0, 1, 2))          # (channels,)
    heatmap = tf.reduce_sum(conv_maps[0] * weights, axis=-1)  # (h, w)
    heatmap = tf.nn.relu(heatmap).numpy()

    peak = heatmap.max()
    return heatmap / peak if peak > 0 else heatmap  # all zeros -> no clear focus


def overlay_heatmap(image: Image.Image, heatmap: np.ndarray, alpha: float = 0.45) -> Image.Image:
    """Blend a colour-mapped heatmap (red = most important) over the original photo."""
    rgb = np.asarray(image.convert("RGB"))
    # Stretch the heatmap back to the photo's size. The model saw a 224x224
    # squashed version, so stretching reverses that mapping.
    heat = cv2.resize(heatmap.astype(np.float32), (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)
    heat = np.uint8(255 * np.clip(heat, 0, 1))
    colored = cv2.cvtColor(cv2.applyColorMap(heat, cv2.COLORMAP_JET), cv2.COLOR_BGR2RGB)
    blended = cv2.addWeighted(colored, alpha, rgb, 1 - alpha, 0)
    return Image.fromarray(blended)
