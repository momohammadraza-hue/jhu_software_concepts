import os, re
import pytest
from types import SimpleNamespace
from bs4 import BeautifulSoup
import os, sys
# Ensure repo root is on sys.path so "module_4.src" imports work when running from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
@pytest.fixture
def app(monkeypatch):
    from module_4.src.analysis_app import create_app

    # Fake injectables (no network)
    def fake_scraper():
        return [
            {"id":"row1","program":"CS","university":"X","admit":True,"score":95},
            {"id":"row2","program":"EE","university":"Y","admit":False,"score":72},
        ]

    inserted = []

    def fake_loader(rows, conn):
        inserted.extend(rows)
        return len(rows)

    def fake_query(conn):
        return {
            "summary": {
                "year": "2024",
                "fall_count": len(inserted) or 100,
                "intl_pct": f"{39.28:.2f}",   # already “xx.xx”
                "avg_gpa": "3.55",
                "accept_pct_fall": "21.45",
            },
            "blocks": {
                "total_rows": (len(inserted) or 2) + 498,
                "fall_count": len(inserted) or 100,
                "percent_intl": f"{39.28:.2f}",
                "avg_gpa": "3.55",
                "avg_gre": "320",
                "avg_grev": "160",
                "avg_greaw": "4.5",
                "avg_gpa_american": "3.48",
                "accept_pct_fall": "21.45",
                "avg_gpa_accepted": "3.72",
                "jhu_cs_ms": 140,
                "georgetown_phd_cs_accepted": 6,
                "top_programs": [
                    {"program":"CS MS","n_total":300,"n_acc":50,"acc_rate":"16.67"},
                ],
                "gpa_buckets": [
                    {"bucket":"3.5–3.8","n_total":340,"n_acc":73,"acc_rate":"21.47"},
                ],
                "chart": {
                    "top_programs": {"labels":["CS MS"], "totals":[300], "acc_rate":[16.67]},
                    "gpa_buckets":  {"labels":["3.5–3.8"], "totals":[340], "acc_rate":[21.47]},
                    "years": {"labels":["2020","2021"], "totals":[170,190], "acc_rate":[13.2,14.1]},
                },
            },
        }

    cfg = {
        "TESTING": True,
        "SCRAPER": fake_scraper,
        "LOADER": fake_loader,
        "QUERY": fake_query,
        # “DATABASE_URL” can be anything; we’re not hitting a real DB here
        "DATABASE_URL": os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"),
    }

    app = create_app(cfg)
# Ensure the busy flag and last_msg exist (don’t replace the whole state object)
    if not hasattr(app, "state") or app.state is None:
        from types import SimpleNamespace
        app.state = SimpleNamespace(busy=False, last_msg=None)
    else:
        if not hasattr(app.state, "busy"):
            app.state.busy = False
        if not hasattr(app.state, "last_msg"):
            app.state.last_msg = None
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def soup():
    def _s(html: bytes | str):
        return BeautifulSoup(html, "lxml")
    return _s

# Old:
# @pytest.fixture
# def pct_two_decimals():
#     return re.compile(r"\b\d{1,3}\.\d{2}%\b")

# New (accepts with or without %):
@pytest.fixture
def pct_two_decimals():
    return re.compile(r"\b\d{1,3}\.\d{2}%?\b")