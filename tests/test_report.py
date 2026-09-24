"""The shareable report, the WhatsApp link and the translated image errors."""

import io
from urllib.parse import unquote

import pytest
from PIL import Image

from utils import i18n, report
from utils.preprocessing import ImageError, load_image


@pytest.fixture
def in_language(monkeypatch):
    """Switch utils.i18n to a language without a Streamlit session."""
    def switch(lang):
        monkeypatch.setattr(i18n, "current", lambda: lang)
        monkeypatch.setattr(report, "current", lambda: lang)
    return switch


@pytest.mark.parametrize("lang", list(i18n.LANGUAGES))
@pytest.mark.parametrize("class_name", ["Tomato___Late_blight", "Tomato___healthy"])
def test_report_contains_the_diagnosis(in_language, leaf_image, lang, class_name):
    in_language(lang)
    entry = i18n.knowledge_base(lang)[class_name]
    html = report.build_report(leaf_image, leaf_image, "leaf.jpg", entry["crop"], entry["disease"], entry,
                               0.93, uncertain=False, helpline=True)
    assert f'<html lang="{lang}">' in html
    assert entry["disease"] in html and report.HELPLINE in html
    assert html.count("data:image/jpeg;base64,") == 2
    if not entry["is_healthy"]:
        assert entry["treatment_chemical"][0] in html


def test_report_escapes_text(in_language, leaf_image):
    in_language("en")
    entry = dict(i18n.knowledge_base("en")["Tomato___Late_blight"], description="<script>x</script>")
    html = report.build_report(leaf_image, leaf_image, "a<b>.jpg", "Tomato", "Late blight", entry, 0.9, False, False)
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_whatsapp_link_carries_the_advice(in_language):
    in_language("hi")
    entry = i18n.knowledge_base("hi")["Tomato___Late_blight"]
    url = report.whatsapp_url(entry["crop"], entry["disease"], entry, 0.81, uncertain=False, helpline=True)
    assert url.startswith("https://wa.me/?text=")
    text = unquote(url.split("=", 1)[1])
    assert entry["disease"] in text and entry["treatment_organic"][0] in text and report.APP_URL in text


def test_report_file_name():
    assert report.file_name("Pepper,_bell___Bacterial_spot").startswith("leafcare-pepper-bell-bacterial-spot-")


@pytest.mark.parametrize("data", [b"not a picture", "tiny"])
def test_image_errors_have_translations(in_language, data):
    if data == "tiny":
        buffer = io.BytesIO()
        Image.new("RGB", (20, 20)).save(buffer, format="PNG")
        data = buffer.getvalue()
    with pytest.raises(ImageError) as caught:
        load_image(data)
    for lang in i18n.LANGUAGES:
        in_language(lang)
        assert i18n.t(f"error.{caught.value.reason}", **caught.value.values)
