import pytest

@pytest.mark.integration
def test_pull_update_then_render(app, client, soup, pct_two_decimals):
    # pull
    app.state.busy = False
    r1 = client.post("/pull")
    assert r1.status_code in (200, 202)
    # update
    r2 = client.post("/update")
    assert r2.status_code == 200
    # render
    r3 = client.get("/analysis")
    assert r3.status_code == 200
    s = soup(r3.data)
    assert "Applicants" in s.text
    assert any(pct_two_decimals.search(t) for t in s.stripped_strings)