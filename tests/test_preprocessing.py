import io
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from utils import preprocessing
from utils.preprocessing import IMG_SIZE, ImageError, image_to_model_input, load_image

ROOT = Path(__file__).resolve().parents[1]


def _png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_model_input_shape_dtype_and_range(leaf_image):
    arr = image_to_model_input(leaf_image)
    assert arr.shape == (IMG_SIZE, IMG_SIZE, 3)
    assert arr.dtype == np.float32
    # EfficientNet rescales internally, so pixels must stay in 0-255 (not 0-1).
    assert 1.0 < arr.max() <= 255.0
    assert np.allclose(arr[0, 0], [70, 140, 60])


def test_load_image_converts_rgba_to_rgb():
    rgba = Image.new("RGBA", (100, 100), (10, 200, 10, 128))
    assert load_image(_png_bytes(rgba)).mode == "RGB"


def test_load_image_rejects_non_image():
    with pytest.raises(ImageError):
        load_image(b"this is definitely not a picture")


def test_load_image_rejects_truncated_file(leaf_image):
    with pytest.raises(ImageError):
        load_image(_png_bytes(leaf_image)[:200])


def test_load_image_rejects_tiny_image():
    with pytest.raises(ImageError, match="very small"):
        load_image(_png_bytes(Image.new("RGB", (20, 20))))


def test_notebook_uses_identical_preprocessing():
    """The Colab notebook must contain an exact copy of the shared preprocess function."""
    start = "# --- shared preprocessing"
    end = "# --- end shared preprocessing ---"

    def shared_block(text: str) -> str:
        return text[text.index(start): text.index(end)]

    source = Path(preprocessing.__file__).read_text()
    notebook = json.loads((ROOT / "notebooks" / "train_model.ipynb").read_text())
    cells = ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]
    matching = [cell for cell in cells if start in cell]
    assert matching, "notebook is missing the shared preprocessing cell"
    assert shared_block(matching[0]) == shared_block(source)
