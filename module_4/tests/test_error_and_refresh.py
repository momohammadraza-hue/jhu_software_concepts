import pytest

@pytest.mark.buttons
def test_pull_returns_500_when_not_configured(app, client):
    # Remove DI functions so /pull hits the 500 branch
    app.config["SCRAPER"] = None
    app.config["LOADER"] = None
    app.state.busy = False
    r = client.post("/pull")
    assert r.status_code == 500
    assert r.is_json and r.json.get("ok") is False

@pytest.mark.buttons
def test_update_calls_refresh_when_provided(app, client):
    calls = {"n": 0}
    def fake_refresh(conn):
        calls["n"] += 1
    app.config["REFRESH"] = fake_refresh
    app.state.busy = False
    r = client.post("/update")
    assert r.status_code == 200
    assert r.is_json and r.json.get("ok") is True
    assert calls["n"] == 1