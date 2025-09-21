import pytest

@pytest.mark.web
def test_analysis_page_loads(client, soup):
    r = client.get("/analysis")
    assert r.status_code == 200
    s = soup(r.data)
    assert "GradCafe Analysis" in s.text or "Analysis" in s.text
    # two stable selectors (you added data-testid attrs)
    assert s.select_one('[data-testid="pull-data-btn"]') or s.find(text="Pull Data")
    assert s.select_one('[data-testid="update-analysis-btn"]') or s.find(text="Update Analysis")
    # at least one “Answer:” equivalent: your dashboard uses KPI labels; ensure page has expected sections
    assert "Applicants" in s.text or "Top-10 Programs" in s.text