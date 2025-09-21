import csv
import io
import pytest

@pytest.mark.web
def test_status_endpoint_reports_busy_flag(app, client):
    app.state.busy = False
    r = client.get("/status")
    assert r.status_code == 200
    assert r.json == {"busy": False}
    app.state.busy = True
    r2 = client.get("/status")
    assert r2.status_code == 200
    assert r2.json == {"busy": True}

@pytest.mark.web
def test_download_csv_returns_csv_with_expected_rows(client):
    r = client.get("/download.csv")
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("text/csv")
    assert "attachment; filename=" in r.headers["Content-Disposition"]
    # sanity-parse first few rows
    buf = io.StringIO(r.data.decode("utf-8"))
    rows = list(csv.reader(buf))
    # has header + some data lines
    assert rows[0] == ["section", "col1", "col2", "col3", "col4"]
    assert any(row and row[0] == "summary" for row in rows[1:])