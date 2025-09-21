"""
Module 4 Flask app (GradCafe Analysis Dashboard).

Goals (per Week 4):
- Factory: create_app(config=None)
- Routes your template expects:
    GET  / and /analysis   -> render index.html
    POST /pull             -> scrape+load (DI), 409 if busy
    POST /update           -> refresh analysis (DI), 409 if busy
    GET  /status           -> {"busy": bool}
    GET  /download.csv     -> CSV snapshot
- Busy-state: simple flag, no sleeps
- Dependency Injection via app.config: SCRAPER, LOADER, QUERY, REFRESH
- Context keys for template: title, busy, msg, summary, blocks (with blocks.chart)
- Percent formatting: exactly two decimals where applicable
"""

from __future__ import annotations

import csv
import io
import os
from types import SimpleNamespace
from typing import Any, Callable, Iterable

from flask import Flask, jsonify, make_response, render_template

try:
    import psycopg  # optional—tests may not need a real DB
except Exception:  # pragma: no cover
    psycopg = None  # type: ignore


# ---------------- helpers ----------------

def _connect(dsn: str):
    """Return a connection if psycopg is available; else None."""
    if psycopg is None:
        return None
    return psycopg.connect(dsn)


def _fmt_pct01(val: float | int | None) -> str | None:
    """Proportion 0..1 -> 'xx.xx' (no % sign)."""
    if val is None:
        return None
    try:
        return f"{float(val) * 100.0:.2f}"
    except Exception:
        return None


def _default_query(_: Any) -> dict:
    """
    Safe fallback so index.html renders even without DB/DI.
    Shape mirrors what the template uses: summary, blocks, blocks.chart.
    """
    years = ["2019", "2020", "2021", "2022", "2023", "2024"]
    totals = [150, 170, 190, 210, 250, 300]
    acc_rate = [12.5, 13.2, 14.1, 15.0, 16.8, 18.2]

    return {
        "summary": {
            "year": years[-1],
            "fall_count": 100,
            "intl_pct": _fmt_pct01(0.3928),
            "avg_gpa": "3.55",
            "accept_pct_fall": "21.45",
        },
        "blocks": {
            "total_rows": sum(totals),
            "fall_count": 100,
            "percent_intl": _fmt_pct01(0.3928),
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
                {"program": "CS MS", "n_total": 300, "n_acc": 50, "acc_rate": "16.67"},
                {"program": "DS MS", "n_total": 200, "n_acc": 30, "acc_rate": "15.00"},
            ],
            "gpa_buckets": [
                {"bucket": "<3.2", "n_total": 100, "n_acc": 5, "acc_rate": "5.00"},
                {"bucket": "3.2–3.5", "n_total": 120, "n_acc": 15, "acc_rate": "12.50"},
            ],
            "chart": {
                "top_programs": {
                    "labels": ["CS MS", "DS MS"],
                    "totals": [300, 200],
                    "acc_rate": [16.67, 15.0],
                },
                "gpa_buckets": {
                    "labels": ["<3.2", "3.2–3.5"],
                    "totals": [100, 120],
                    "acc_rate": [5.0, 12.5],
                },
                "years": {
                    "labels": years,
                    "totals": totals,
                    "acc_rate": acc_rate,
                },
            },
        },
    }


# --------------- factory ---------------

def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config.update(
        TESTING=False,
        DATABASE_URL=os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/postgres",
        ),
        # DI hooks (tests or prod can provide these):
        SCRAPER=None,   # () -> Iterable[dict]
        LOADER=None,    # (rows, conn) -> int
        QUERY=None,     # (conn) -> dict (summary/blocks/chart)
        REFRESH=None,   # optional: (conn) -> None
    )
    if config:
        app.config.update(config)

    # Simple, observable busy flag (no sleeps)
    app.state = getattr(app, "state", SimpleNamespace(busy=False))
    app.state.last_msg = None

    # --------------- routes ---------------

    @app.get("/")
    @app.get("/analysis")
    def analysis_page():
        """Render dashboard with {title,busy,msg,summary,blocks}."""
        query_fn: Callable[[Any], dict] | None = app.config.get("QUERY")
        conn = None
        try:
            conn = _connect(app.config["DATABASE_URL"]) if query_fn else None
            analysis = query_fn(conn) if query_fn else _default_query(None)
        finally:
            if conn is not None:
                conn.close()

        ctx = {
            "title": "GradCafe Analysis",
            "busy": app.state.busy,
            "msg": app.state.last_msg,
            "summary": analysis.get("summary", {}),
            "blocks": analysis.get("blocks", {}),
        }
        # one-shot banner
        app.state.last_msg = None
        return render_template("index.html", **ctx)

    @app.post("/pull")
    def pull():
        """Kick off scrape+load. 409 if already busy."""
        if app.state.busy:
            return jsonify({"busy": True}), 409

        scraper: Callable[[], Iterable[dict]] | None = app.config.get("SCRAPER")
        loader: Callable[[Iterable[dict], Any], int] | None = app.config.get("LOADER")
        if not scraper or not loader:
            return jsonify({"ok": False, "error": "SCRAPER/LOADER not configured"}), 500

        app.state.busy = True
        conn = None
        try:
            rows = list(scraper())
            conn = _connect(app.config["DATABASE_URL"])
            inserted = loader(rows, conn)
            app.state.last_msg = f"Pulled and inserted {inserted} rows."
            return jsonify({"ok": True, "inserted": inserted}), 200
        finally:
            app.state.busy = False
            if conn is not None:
                conn.close()

    @app.post("/update")
    def update():
        """Recompute/refresh analysis. 409 if busy."""
        if app.state.busy:
            return jsonify({"busy": True}), 409

        refresh: Callable[[Any], None] | None = app.config.get("REFRESH")
        if refresh:
            conn = _connect(app.config["DATABASE_URL"])
            try:
                refresh(conn)
            finally:
                if conn:
                    conn.close()
        app.state.last_msg = "Analysis updated."
        return jsonify({"ok": True}), 200

    @app.get("/status")
    def status():
        """Busy flag for client polling."""
        return jsonify({"busy": bool(app.state.busy)}), 200

    @app.get("/download.csv")
    def download_csv():
        """CSV snapshot from QUERY results (simple, template-aligned)."""
        query_fn: Callable[[Any], dict] | None = app.config.get("QUERY")
        conn = None
        try:
            conn = _connect(app.config["DATABASE_URL"]) if query_fn else None
            analysis = query_fn(conn) if query_fn else _default_query(None)
        finally:
            if conn:
                conn.close()

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["section", "col1", "col2", "col3", "col4"])
        s = analysis.get("summary", {})
        w.writerow(["summary", "year", s.get("year"), "", ""])
        w.writerow(["summary", "intl_pct", s.get("intl_pct"), "", ""])
        for r in analysis.get("blocks", {}).get("top_programs", []):
            w.writerow(["top_programs", r.get("program"), r.get("n_total"), r.get("n_acc"), r.get("acc_rate")])

        out = make_response(buf.getvalue())
        out.headers["Content-Type"] = "text/csv"
        out.headers["Content-Disposition"] = "attachment; filename=gradcafe_export.csv"
        return out

    return app