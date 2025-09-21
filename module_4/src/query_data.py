# module_3_new/query_data.py
"""Module 3 — SQL Data Analysis (psycopg 3).

Implements Q1–Q8 from the assignment (Fall 2025) plus two extra analyses.
Assumes:
- `applicants` loaded via load_data.py
- `applicants_norm` and `applicants_valid` views exist
- Normalized fields in `program_norm` / `university_norm`
"""

from __future__ import annotations

import os
from typing import Iterable, Sequence, Tuple

import psycopg

DSN = os.getenv("DSN", "postgresql://localhost/gradcafe")
YEAR = 2025  # assignment requires Fall 2025


QUERIES: Sequence[Tuple[str, str, Tuple]] = [
    (
        "Q1: Fall 2025 applicant count",
        """
        SELECT COUNT(*)
        FROM applicants_valid
        WHERE term_norm = 'Fall' AND year_guess = %s;
        """,
        (YEAR,),
    ),
    (
        "Q2: Percent International (two decimals, all-time)",
        """
        WITH base AS (SELECT COUNT(*) AS n_all FROM applicants_valid),
             intl AS (
               SELECT COUNT(*) AS n_intl
               FROM applicants_valid
               WHERE COALESCE(us_or_international, '') ILIKE '%%international%%'
             )
        SELECT ROUND((intl.n_intl::numeric / NULLIF(base.n_all, 0)) * 100, 2)
        FROM base, intl;
        """,
        (),
    ),
    (
        "Q3: Avg GPA / GRE / GRE V / GRE AW (all-time)",
        """
        SELECT
          ROUND(AVG(gpa)::numeric,    2),
          ROUND(AVG(gre)::numeric,    2),
          ROUND(AVG(gre_v)::numeric,  2),
          ROUND(AVG(gre_aw)::numeric, 2)
        FROM applicants_valid;
        """,
        (),
    ),
    (
        "Q4: Avg GPA of American students — Fall 2025",
        """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants_valid
        WHERE term_norm = 'Fall'
          AND year_guess = %s
          AND COALESCE(us_or_international, '') ILIKE '%%american%%';
        """,
        (YEAR,),
    ),
    (
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
        SELECT ROUND((acc.n_acc::numeric / NULLIF(base.n_all, 0)) * 100, 2)
        FROM base, acc;
        """,
        (YEAR, YEAR),
    ),
    (
        "Q6: Avg GPA among Accepted — Fall 2025",
        """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants_valid
        WHERE term_norm = 'Fall'
          AND year_guess = %s
          AND status_norm = 'Accepted';
        """,
        (YEAR,),
    ),
    (
        "Q7: JHU Masters in Computer Science (all-time, normalized)",
        """
        SELECT COUNT(*)
        FROM applicants_valid
        WHERE COALESCE(university_norm, '') ILIKE '%%Johns Hopkins%%'
          AND COALESCE(program_norm,   '') ILIKE '%%Computer Science%%'
          AND COALESCE(degree,         '') ILIKE '%%master%%';
        """,
        (),
    ),
    (
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
    ),
    (
        "Q9 (extra): Top-10 programs by volume (all-time) + acceptance rate",
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
          ROUND((n_acc::numeric / NULLIF(n_total, 0)) * 100, 2) AS acc_rate_pct
        FROM prog
        ORDER BY n_total DESC
        LIMIT 10;
        """,
        (),
    ),
    (
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
          ROUND((n_acc::numeric / NULLIF(n_total, 0)) * 100, 2) AS acc_rate_pct
        FROM agg
        ORDER BY CASE gpa_bucket
                   WHEN 'No GPA'    THEN 0
                   WHEN '<3.0'      THEN 1
                   WHEN '3.0–3.49'  THEN 2
                   WHEN '3.5–3.79'  THEN 3
                   WHEN '>=3.8'     THEN 4
                 END;
        """,
        (),
    ),
]


def main() -> None:
    """Execute all queries and print results."""
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        for title, sql, params in QUERIES:
            print(f"\n{title}")
            cur.execute(sql, params)
            for row in cur.fetchall():
                print(row)


if __name__ == "__main__":
    main()