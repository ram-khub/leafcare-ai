"""Image loading and preprocessing shared by training and inference.

The model must see images prepared in EXACTLY the same way during training
(in the Colab notebook) and in the app. `preprocess` below is copied verbatim
into notebooks/train_model.ipynb, and tests/test_preprocessing.py fails if the
two copies ever drift apart.

Note: Keras' EfficientNet models contain their own rescaling layer and expect
raw pixel values in the 0-255 range. So we only resize here, we do NOT divide
by 255 or normalise (doing so would "double-normalise" the input).
"""

import io

import numpy as np
import tensorflow as tf
from PIL import Image, ImageOps, UnidentifiedImageError

IMG_SIZE = 224          # model input is IMG_SIZE x IMG_SIZE x 3
MIN_IMAGE_SIDE = 64     # smaller uploads carry too little detail to diagnose


class ImageError(ValueError):
    """Raised when an uploaded file can't be used; the message is user-friendly."""


# --- shared preprocessing (must be identical in app/utils/preprocessing.py and notebooks/train_model.ipynb) ---
def preprocess(image):
    """Resize an RGB image tensor (H, W, 3) to the model input: float32, 224x224x3, values 0-255."""
    image = tf.image.resize(image, (IMG_SIZE, IMG_SIZE), method="bilinear")
    return tf.cast(image, tf.float32)
# --- end shared preprocessing ---


def load_image(data: bytes) -> Image.Image:
    """Decode uploaded bytes into an upright RGB PIL image, or raise ImageError."""
    try:
        image = Image.open(io.BytesIO(data))
        image.load()  # force a full decode so truncated/corrupt files fail here
    except (UnidentifiedImageError, OSError, ValueError) as err:
        raise ImageError(
            "We couldn't read that file. Please upload a JPG or PNG photo of a leaf."
        ) from err

    image = ImageOps.exif_transpose(image)  # respect phone camera rotation

    if min(image.size) < MIN_IMAGE_SIDE:
        raise ImageError(
            f"That image is very small ({image.width}x{image.height} px). "
            f"Please use a photo at least {MIN_IMAGE_SIDE} px on each side."
        )

    # Flatten transparency onto white and convert greyscale/CMYK/etc. to RGB.
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.getchannel("A"))
        image = background
    return image.convert("RGB")


def image_to_model_input(image: Image.Image) -> np.ndarray:
    """PIL RGB image -> float32 array of shape (224, 224, 3) ready for the model."""
    return preprocess(np.asarray(image, dtype=np.uint8)).numpy()
