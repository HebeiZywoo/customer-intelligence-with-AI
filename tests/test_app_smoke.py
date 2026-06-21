"""End-to-end smoke test for the Streamlit dashboard.

Uses Streamlit's AppTest harness to execute the whole app headlessly, exercising
every tab, chart, and table render. Marked ``slow`` because, on a clean
checkout, the app regenerates the dataset on first run.
"""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

APP = "app/streamlit_app.py"


@pytest.mark.slow
def test_dashboard_runs_without_exceptions() -> None:
    app = AppTest.from_file(APP, default_timeout=180).run()
    assert not app.exception, app.exception
    assert len(app.tabs) == 6
