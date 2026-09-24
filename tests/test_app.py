"""Smoke test: every page of the Streamlit app renders without an exception."""

import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["views/1_Scan_History.py", "views/2_About_the_Model.py", "views/3_SDG_Impact.py", "views/4_Feedback.py"]


def test_diagnose_page_with_sample_image():
    app = AppTest.from_file("../app/Home.py", default_timeout=60).run()
    assert not app.exception
    app.session_state["input_mode"] = ":material/eco: Try a sample"
    app.run()
    app.button[0].click().run()  # "Use this" on the first sample
    assert not app.exception
    assert len(app.session_state["history"]) == 1  # the scan was recorded


def test_scan_another_leaf_clears_the_photo():
    app = AppTest.from_file("../app/Home.py", default_timeout=60).run()
    app.session_state["input_mode"] = ":material/eco: Try a sample"
    app.run()
    app.button[0].click().run()  # "Use this" on the first sample
    next(b for b in app.button if b.label == "Scan another leaf").click().run()
    assert not app.exception
    assert "sample" not in app.session_state
    assert not any(b.label == "Scan another leaf" for b in app.button)  # back to Step 1, no result shown


def test_clear_history_needs_confirmation():
    app = AppTest.from_file("../app/Home.py", default_timeout=60).run()
    app.session_state["input_mode"] = ":material/eco: Try a sample"
    app.run()
    app.button[0].click().run()
    app.switch_page("views/1_Scan_History.py").run()
    assert len(app.session_state["history"]) == 1  # opening the page (and the popover) clears nothing
    next(b for b in app.button if b.label == "Yes, clear").click().run()
    assert not app.exception
    assert app.session_state["history"] == []


@pytest.mark.parametrize("page", PAGES)
def test_other_pages_render(page):
    app = AppTest.from_file("../app/Home.py", default_timeout=60).run()
    app.switch_page(page).run()
    assert not app.exception


@pytest.mark.parametrize("asset", ["styles.css", "theme_switch.js", "read_aloud.js", "copy_text.js", "help_tips.js"])
def test_injected_assets_survive_sanitiser(asset):
    """st.html sanitises with DOMPurify, which silently drops a style/script block containing tag-like text."""
    import re

    from utils.ui import ASSETS

    assert not re.search(r"<[/\w!]", (ASSETS / asset).read_text())


def test_feedback_form_confirms():
    # Clearing the box is done by the browser (clear_on_submit), which AppTest doesn't simulate.
    app = AppTest.from_file("../app/Home.py", default_timeout=60).run()
    app.switch_page("views/4_Feedback.py").run()
    app.text_area[0].input("The heatmap is great").run()
    app.button[0].click().run()
    assert not app.exception
    assert any("Feedback received" in el.body for el in app.get("html"))
