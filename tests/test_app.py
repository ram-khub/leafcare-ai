"""Smoke test: every page of the Streamlit app renders without an exception."""

import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["pages/1_Scan_History.py", "pages/2_About_the_Model.py", "pages/3_SDG_Impact.py"]


def test_diagnose_page_with_sample_image():
    app = AppTest.from_file("../app/Home.py", default_timeout=60).run()
    assert not app.exception
    app.session_state["input_mode"] = ":material/eco: Try a sample"
    app.run()
    app.button[0].click().run()  # "Use this" on the first sample
    assert not app.exception
    assert len(app.session_state["history"]) == 1  # the scan was recorded


@pytest.mark.parametrize("page", PAGES)
def test_other_pages_render(page):
    app = AppTest.from_file("../app/Home.py", default_timeout=60).run()
    app.switch_page(page).run()
    assert not app.exception
