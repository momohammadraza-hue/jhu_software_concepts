import pytest

@pytest.mark.buttons
def test_pull_ok_when_idle(app, client):
    app.state.busy = False
    r = client.post("/pull")
    assert r.status_code in (200, 202)
    assert r.is_json and r.json.get("ok") is True

@pytest.mark.buttons
def test_update_ok_when_idle(app, client):
    app.state.busy = False
    r = client.post("/update")
    assert r.status_code == 200
    assert r.json.get("ok") is True

@pytest.mark.buttons
def test_busy_returns_409(app, client):
    app.state.busy = True
    assert client.post("/pull").status_code == 409
    assert client.post("/update").status_code == 409