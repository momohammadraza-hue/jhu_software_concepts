import pytest
import re

@pytest.mark.analysis
def test_two_decimal_percentages(client, soup):
    r = client.get("/analysis")
    s = soup(r.data)
    # Accept either "xx.xx%" or plain "xx.xx" (some templates add % in CSS/labels)
    rx = re.compile(r"\b\d{1,3}\.\d{2}%?\b")
    assert any(rx.search(t) for t in s.stripped_strings)