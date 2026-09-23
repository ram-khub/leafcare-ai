"""Create a tiny, UNTRAINED stand-in model so the app runs before real training.

It has the same interface as the real EfficientNetB0 model:
  input  (224, 224, 3) raw 0-255 pixels
  output (38,) softmax over models/class_names.json
  a conv layer named "top_conv" for Grad-CAM

Its predictions are meaningless. Replace models/leaf_model.keras with the file
exported from the Colab notebook and the app uses the real model; no code changes.

Also draws simple placeholder leaf pictures into app/assets/sample_images/
(only if that folder is empty) so the "Try a sample" buttons have something to show.

Run from the project root:  python scripts/make_placeholder_model.py
"""

import json
import math
import random
from pathlib import Path

import keras
from keras import layers
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "leaf_model.keras"
CLASS_NAMES_PATH = ROOT / "models" / "class_names.json"
SAMPLES_DIR = ROOT / "app" / "assets" / "sample_images"
IMG_SIZE = 224


def build_placeholder_model(num_classes: int, output_scale: float = 16.0) -> keras.Model:
    keras.utils.set_random_seed(42)  # same placeholder every time
    inputs = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3), name="image")
    x = layers.Rescaling(1 / 255)(inputs)  # the real EfficientNet rescales internally too
    for filters in (8, 16, 32):
        x = layers.Conv2D(filters, 3, strides=2, padding="same", activation="relu")(x)
    x = layers.Conv2D(64, 3, strides=2, padding="same", activation="relu", name="top_conv")(x)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    # Scaled-up random weights give a top-class probability of roughly 70%, so the
    # app's full result card is visible in demo mode (the prediction is still random).
    outputs = layers.Dense(
        num_classes, activation="softmax",
        kernel_initializer=keras.initializers.RandomNormal(stddev=output_scale),
    )(x)
    return keras.Model(inputs, outputs, name="leafcare_placeholder")


def draw_leaf(spots: int, spot_color: tuple, seed: int) -> Image.Image:
    """Draw a simple stylised leaf on a plain background (placeholder art only)."""
    rng = random.Random(seed)
    size = 480
    img = Image.new("RGB", (size, size), (244, 240, 230))
    draw = ImageDraw.Draw(img)

    # Leaf outline: pointed at both ends, widest in the middle.
    cx, cy, length, width = size / 2, size / 2, 380, 210
    angle = math.radians(rng.uniform(-35, 35))
    outline = []
    for i in range(101):
        t = i / 100
        along = (t - 0.5) * length
        half = (width / 2) * math.sin(math.pi * t) ** 0.8
        outline.append((along, half))
    outline += [(a, -h) for a, h in reversed(outline)]

    def rotate(a, h):
        return (cx + a * math.cos(angle) - h * math.sin(angle), cy + a * math.sin(angle) + h * math.cos(angle))

    draw.polygon([rotate(a, h) for a, h in outline], fill=(74, 140, 70))
    # Midrib and side veins.
    draw.line([rotate(-length / 2, 0), rotate(length / 2, 0)], fill=(150, 196, 120), width=4)
    for k in range(-4, 5):
        start = k * 38
        draw.line([rotate(start, 0), rotate(start + 45, 70)], fill=(120, 175, 100), width=2)
        draw.line([rotate(start, 0), rotate(start + 45, -70)], fill=(120, 175, 100), width=2)

    # Disease spots: yellow halo with a darker centre.
    for _ in range(spots):
        a, h = rng.uniform(-140, 140), rng.uniform(-55, 55)
        x, y = rotate(a, h)
        r = rng.uniform(8, 20)
        draw.ellipse([x - r * 1.6, y - r * 1.6, x + r * 1.6, y + r * 1.6], fill=(196, 190, 90))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=spot_color)
    return img.filter(ImageFilter.GaussianBlur(0.8))


def make_sample_images() -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    if any(SAMPLES_DIR.iterdir()):
        print(f"Sample images already present in {SAMPLES_DIR}, leaving them alone.")
        return
    samples = {
        "placeholder_healthy_leaf": (0, (0, 0, 0)),
        "placeholder_brown_spots": (9, (110, 70, 40)),
        "placeholder_dark_lesions": (5, (50, 40, 30)),
        "placeholder_rust_spots": (18, (180, 100, 40)),
    }
    for seed, (name, (spots, color)) in enumerate(samples.items()):
        draw_leaf(spots, color, seed).save(SAMPLES_DIR / f"{name}.jpg", quality=90)
    print(f"Drew {len(samples)} placeholder sample images in {SAMPLES_DIR}")


def main() -> None:
    class_names = json.loads(CLASS_NAMES_PATH.read_text())
    model = build_placeholder_model(len(class_names))
    model.save(MODEL_PATH)
    print(f"Saved placeholder model ({model.count_params():,} params, "
          f"{len(class_names)} classes) to {MODEL_PATH}")
    make_sample_images()


if __name__ == "__main__":
    main()
