import importlib
import types
import pytest

# Import the helpers directly
from module_4.src.analysis_app import _fmt_pct01, _default_query, _connect

@pytest.mark.analysis
def test_fmt_pct01_edges():
    # None → None
    assert _fmt_pct01(None) is None
    # numeric proportion → two-decimal string (no % sign)
    assert _fmt_pct01(0.3928) == "39.28"
    # bad input routes through exception branch → None
    class Weird:
        def __float__(self):  # raise to hit except
            raise ValueError("nope")
    assert _fmt_pct01(Weird()) is None

@pytest.mark.web
def test_default_query_path_renders_when_no_QUERY():
    # Build an app WITHOUT injecting QUERY so default path runs
    from module_4.src.analysis_app import create_app
    app = create_app({"TESTING": True, "QUERY": None})
    client = app.test_client()
    r = client.get("/analysis")
    assert r.status_code == 200
    # default context contains some of these strings
    assert b"GradCafe Analysis" in r.data
    assert b"Applicants" in r.data or b"Results" in r.data or b"summary" in r.data

@pytest.mark.web
def test_connect_when_psycopg_is_none(monkeypatch):
    # Temporarily simulate environment where psycopg is unavailable
    import module_4.src.analysis_app as mod
    monkeypatch.setattr(mod, "psycopg", None, raising=False)
    assert _connect("postgresql://ignored") is None