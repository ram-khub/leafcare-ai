"""Shared pytest fixtures. Makes `utils.*` importable exactly as the Streamlit app does."""

import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from utils.predict import load_class_names, load_model  # noqa: E402


@pytest.fixture(scope="session")
def model():
    return load_model()  # placeholder or real model, both must pass


@pytest.fixture(scope="session")
def class_names():
    return load_class_names()


@pytest.fixture
def leaf_image():
    """A 300x200 green-ish RGB image standing in for a leaf photo."""
    return Image.new("RGB", (300, 200), (70, 140, 60))
