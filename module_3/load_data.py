"""
Module 3 — Load cleaned GradCafe data into PostgreSQL.

Purpose:
    • Read the cleaned CSV from Module 2 (gradcafe_cleaned.csv).
    • Insert rows into the applicants table in the 'gradcafe' database.
    • Handle conversions for dates and floats.
    • Skip rows if the p_id already exists (ON CONFLICT DO NOTHING).

Usage:
    python module_3/load_data.py module_2/data/gradcafe_cleaned.csv
"""

from __future__ import annotations

import sys
import csv
import datetime
import psycopg


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def to_date(v: str | None):
    """
    Convert string values into a Python date.

    Accepts common formats: YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY.
    Returns None if no parse succeeds.
    """
    if not v:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(v, fmt).date()
        except Exception:
            continue
    return None


def to_float(v: str | None):
    """
    Convert string values into a float.

    Accepts numeric strings or returns None for NA, N/A, etc.
    """
    if v in (None, "", "NA", "N/A"):
        return None
    try:
        return float(v)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Core loader
# ---------------------------------------------------------------------------

def load_data(path: str) -> int:
    """
    Load cleaned CSV into the 'gradcafe' PostgreSQL database.

    Args:
        path: Path to the cleaned CSV file.

    Returns:
        Number of rows attempted to insert.
    """
    rows = 0

    # Connect to the local DB created earlier: 'gradcafe'.
    with psycopg.connect("dbname=gradcafe") as conn:
        with conn.cursor() as cur, open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Iterate through CSV rows and insert each into the applicants table.
            for row in reader:
                cur.execute(
                    """
                    INSERT INTO applicants (
                      p_id, program, comments, date_added, url, status, term,
                      us_or_international, gpa, gre, gre_v, gre_aw, degree,
                      llm_generated_program, llm_generated_university
                    )
                    VALUES (
                      %(p_id)s, %(program)s, %(comments)s, %(date_added)s, %(url)s, %(status)s, %(term)s,
                      %(us_or_international)s, %(gpa)s, %(gre)s, %(gre_v)s, %(gre_aw)s, %(degree)s,
                      %(llm_generated_program)s, %(llm_generated_university)s
                    )
                    ON CONFLICT (p_id) DO NOTHING
                    """,
                    {
                        "p_id": int(row["p_id"]),
                        "program": row.get("program"),
                        "comments": row.get("comments"),
                        "date_added": to_date(row.get("date_added")),
                        "url": row.get("url"),
                        "status": row.get("status"),
                        "term": row.get("term"),
                        "us_or_international": row.get("us_or_international"),
                        "gpa": to_float(row.get("gpa")),
                        "gre": to_float(row.get("gre")),
                        "gre_v": to_float(row.get("gre_v")),
                        "gre_aw": to_float(row.get("gre_aw")),
                        "degree": row.get("degree"),
                        "llm_generated_program": row.get("llm_generated_program"),
                        "llm_generated_university": row.get("llm_generated_university"),
                    },
                )
                rows += 1

        # Commit all inserts as one transaction.
        conn.commit()

    print(f"Inserted up to {rows} rows (existing p_id skipped).")
    return rows


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python module_3/load_data.py module_2/data/gradcafe_cleaned.csv")
        sys.exit(1)

    load_data(sys.argv[1])