# module_3_new/analysis_app.py
"""Flask front page for Module 3 analysis.

- Shows Q1–Q10 results.
- Provides two actions:
  * /pull   → runs Module 2 pipeline (scrape → clean → LLM → load)
  * /update → refreshes results (no-op if a pull is running)

Notes:
- Reuses `module_3_new/llm_hosting/app.py` (copied from Module 2).
- Uses psycopg (v3) for PostgreSQL access.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import threading
from typing import Iterable, List, Sequence, Tuple

import psycopg
from flask import Flask, redirect, render_template, url_for

DSN = os.getenv("DSN", "postgresql://localhost/gradcafe")
YEAR = 2025  # assignment requires Fall 2025


app = Flask(__name__)

_pull_lock = threading.Lock()
_pull_running = False


def _exec(cur: psycopg.Cursor, title: str, sql: str,
          params: Sequence = ()) -> dict:
    """Run a SQL statement and return a display block with title + rows."""
    cur.execute(sql, params)
    rows = cur.fetchall()
    return {"title": title, "rows": rows}


def _fetch_all() -> List[dict]:
    """Run all Q1–Q10 queries and return a list of display blocks."""
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        blocks: List[dict] = []

        blocks.append(
            _exec(
                cur,
                "Q1: Fall 2025 applicant count",
                """
                SELECT COUNT(*)
                FROM applicants_valid
                WHERE term_norm = 'Fall' AND year_guess = %s;
                """,
                (YEAR,),
            )
        )

        blocks.append(
            _exec(
                cur,
                "Q2: Percent International (two decimals, all-time)",
                """
                WITH base AS (
                  SELECT COUNT(*) AS n_all FROM applicants_valid
                ),
                intl AS (
                  SELECT COUNT(*) AS n_intl
                  FROM applicants_valid
                  WHERE COALESCE(us_or_international, '') ILIKE '%%international%%'
                )
                SELECT ROUND(
                         (intl.n_intl::numeric / NULLIF(base.n_all, 0)) * 100,
                         2
                       )
                FROM base, intl;
                """,
            )
        )

        blocks.append(
            _exec(
                cur,
                "Q3: Avg GPA / GRE / GRE V / GRE AW (all-time)",
                """
                SELECT
                  ROUND(AVG(gpa)::numeric,    2),
                  ROUND(AVG(gre)::numeric,    2),
                  ROUND(AVG(gre_v)::numeric,  2),
                  ROUND(AVG(gre_aw)::numeric, 2)
                FROM applicants_valid;
                """,
            )
        )

        blocks.append(
            _exec(
                cur,
                "Q4: Avg GPA of American students — Fall 2025",
                """
                SELECT ROUND(AVG(gpa)::numeric, 2)
                FROM applicants_valid
                WHERE term_norm = 'Fall'
                  AND year_guess = %s
                  AND COALESCE(us_or_international, '') ILIKE '%%american%%';
                """,
                (YEAR,),
            )
        )

        blocks.append(
            _exec(
                cur,
                "Q5: Acceptance percent — Fall 2025",
                """
                WITH base AS (
                  SELECT COUNT(*) AS n_all
                  FROM applicants_valid
                  WHERE term_norm = 'Fall' AND year_guess = %s
                ),
                acc AS (
                  SELECT COUNT(*) AS n_acc
                  FROM applicants_valid
                  WHERE term_norm = 'Fall'
                    AND year_guess = %s
                    AND status_norm = 'Accepted'
                )
                SELECT ROUND(
                         (acc.n_acc::numeric / NULLIF(base.n_all, 0)) * 100,
                         2
                       )
                FROM base, acc;
                """,
                (YEAR, YEAR),
            )
        )

        blocks.append(
            _exec(
                cur,
                "Q6: Avg GPA among Accepted — Fall 2025",
                """
                SELECT ROUND(AVG(gpa)::numeric, 2)
                FROM applicants_valid
                WHERE term_norm = 'Fall'
                  AND year_guess = %s
                  AND status_norm = 'Accepted';
                """,
                (YEAR,),
            )
        )

        blocks.append(
            _exec(
                cur,
                "Q7: JHU Masters in Computer Science (all-time, normalized)",
                """
                SELECT COUNT(*)
                FROM applicants_valid
                WHERE COALESCE(university_norm, '') ILIKE '%%Johns Hopkins%%'
                  AND COALESCE(program_norm,   '') ILIKE '%%Computer Science%%'
                  AND COALESCE(degree,         '') ILIKE '%%master%%';
                """,
            )
        )

        blocks.append(
            _exec(
                cur,
                "Q8: 2025 acceptances — Georgetown PhD Computer Science",
                """
                SELECT COUNT(*)
                FROM applicants_valid
                WHERE year_guess = %s
                  AND status_norm = 'Accepted'
                  AND COALESCE(university_norm, '') ILIKE '%%Georgetown%%'
                  AND COALESCE(program_norm,    '') ILIKE '%%Computer Science%%'
                  AND COALESCE(degree,          '') ILIKE '%%phd%%';
                """,
                (YEAR,),
            )
        )

        blocks.append(
            _exec(
                cur,
                "Q9 (extra): Top-10 programs by volume (all-time) "
                "+ acceptance rate",
                """
                WITH prog AS (
                  SELECT
                    program_norm,
                    COUNT(*)                           AS n_total,
                    SUM((status_norm = 'Accepted')::int) AS n_acc
                  FROM applicants_valid
                  WHERE program_norm IS NOT NULL
                  GROUP BY program_norm
                )
                SELECT
                  program_norm,
                  n_total,
                  n_acc,
                  ROUND((n_acc::numeric / NULLIF(n_total, 0)) * 100, 2)
                    AS acc_rate_pct
                FROM prog
                ORDER BY n_total DESC
                LIMIT 10;
                """,
            )
        )

        blocks.append(
            _exec(
                cur,
                "Q10 (extra): Acceptance rate by GPA bucket (all-time)",
                """
                WITH buck AS (
                  SELECT
                    CASE
                      WHEN gpa IS NULL THEN 'No GPA'
                      WHEN gpa < 3.0  THEN '<3.0'
                      WHEN gpa < 3.5  THEN '3.0–3.49'
                      WHEN gpa < 3.8  THEN '3.5–3.79'
                      ELSE                 '>=3.8'
                    END AS gpa_bucket,
                    status_norm
                  FROM applicants_valid
                ),
                agg AS (
                  SELECT
                    gpa_bucket,
                    COUNT(*) AS n_total,
                    SUM((status_norm = 'Accepted')::int) AS n_acc
                  FROM buck
                  GROUP BY gpa_bucket
                )
                SELECT
                  gpa_bucket,
                  n_total,
                  n_acc,
                  ROUND((n_acc::numeric / NULLIF(n_total, 0)) * 100, 2)
                    AS acc_rate_pct
                FROM agg
                ORDER BY CASE gpa_bucket
                           WHEN 'No GPA'    THEN 0
                           WHEN '<3.0'      THEN 1
                           WHEN '3.0–3.49'  THEN 2
                           WHEN '3.5–3.79'  THEN 3
                           WHEN '>=3.8'     THEN 4
                         END;
                """,
            )
        )

        return blocks


def _run(cmd: str) -> str:
    """Run a shell command and return stdout, raising on non-zero exit."""
    print(">>", cmd)
    proc = subprocess.run(
        shlex.split(cmd),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{cmd}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def _pull_pipeline() -> None:
    """Execute the Module 2→3 pipeline in a background thread."""
    global _pull_running
    try:
        _run(
            "python module_2_new/scrape.py --q 'computer science' "
            "--pages 1 --out module_2_new/applicant_data.json"
        )
        _run(
            "python module_2_new/clean.py "
            "--src module_2_new/applicant_data.json "
            "--out module_2_new/data/gradcafe_cleaned.csv "
            "--llm_prep module_2_new/data/clean_for_llm.jsonl"
        )
        _run(
            "python module_3_new/llm_hosting/app.py "
            "--file module_2_new/data/clean_for_llm.jsonl "
            "--out module_2_new/data/llm_extended.jsonl"
        )
        _run(
            f"python module_3_new/load_data.py "
            f"--csv module_2_new/data/gradcafe_cleaned.csv "
            f"--llm-jsonl module_2_new/data/llm_extended.jsonl "
            f"--dsn {DSN}"
        )
    finally:
        with _pull_lock:
            _pull_running = False


@app.get("/")
def index():
    """Render the analysis page with current results and button state."""
    with psycopg.connect(DSN) as _conn, _conn.cursor() as _cur:
        results = _fetch_all()
    with _pull_lock:
        running = _pull_running
    return render_template(
        "index.html",
        results=results,
        pull_running=running,
        year=YEAR,
    )


@app.post("/pull")
def pull():
    """Kick off a background pull unless one is already running."""
    global _pull_running
    with _pull_lock:
        if _pull_running:
            return redirect(url_for("index"))
        _pull_running = True
    thread = threading.Thread(target=_pull_pipeline, daemon=True)
    thread.start()
    return redirect(url_for("index"))


@app.post("/update")
def update():
    """Refresh results (no-op if a pull is running since index re-queries)."""
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=False)