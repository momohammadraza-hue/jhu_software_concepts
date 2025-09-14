"""
Module 3 — Query analytics for the GradCafe database.

Purpose:
    • Provide a small set of reusable query functions against the 'applicants'
      table in the 'gradcafe' PostgreSQL database.
    • Print representative results when run as a script.

Notes:
    • Queries assume columns created by your Module 2 -> Module 3 pipeline.
    • Connection string uses the local DB name 'gradcafe'.
"""

from __future__ import annotations

import json
import psycopg

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _conn():
    """Create a new connection to the local 'gradcafe' database."""
    return psycopg.connect("dbname=gradcafe")


def one(sql: str, params: dict | None = None):
    """
    Execute a query that returns a single scalar value.

    Args:
        sql: SQL text with optional %(name)s placeholders.
        params: Optional dict of parameters.

    Returns:
        The first column of the first row, or None if no row.
    """
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(sql, params or {})
        row = cur.fetchone()
        return row[0] if row else None


def j(obj) -> str:
    """Pretty-print as JSON for terminal output."""
    return json.dumps(obj, indent=2, default=str)

# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------

def q1():
    """Q1. How many entries applied for Fall 2025?"""
    return one("SELECT COUNT(*) FROM applicants WHERE term ILIKE 'Fall 2025%%';")


def q2():
    """Q2. Percentage of international (not American or Other), two decimals."""
    num = one(
        """
        SELECT COUNT(*) FROM applicants
        WHERE COALESCE(us_or_international,'') NOT ILIKE ANY(ARRAY['%%American%%','%%Other%%']);
        """
    )
    den = one("SELECT COUNT(*) FROM applicants;")
    return round((num or 0) * 100.0 / (den or 1), 2)


def q3():
    """Q3. Average GPA, GRE, GRE V, GRE AW (non-null)."""
    return one(
        """
        SELECT json_build_object(
          'gpa',    ROUND(AVG(gpa)::numeric, 2),
          'gre',    ROUND(AVG(gre)::numeric, 2),
          'gre_v',  ROUND(AVG(gre_v)::numeric, 2),
          'gre_aw', ROUND(AVG(gre_aw)::numeric, 2)
        )
        FROM applicants;
        """
    )


def q4():
    """Q4. Average GPA of American students in Fall 2025."""
    return one(
        """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE term ILIKE 'Fall 2025%%'
          AND us_or_international ILIKE '%%American%%';
        """
    )


def q5():
    """Q5. Percentage of acceptances for Fall 2025 (two decimals)."""
    acc = one(
        """
        SELECT COUNT(*) FROM applicants
        WHERE term ILIKE 'Fall 2025%%'
          AND status ILIKE 'Accept%%';
        """
    )
    den = one(
        """
        SELECT COUNT(*) FROM applicants
        WHERE term ILIKE 'Fall 2025%%';
        """
    )
    return round((acc or 0) * 100.0 / (den or 1), 2)


def q6():
    """Q6. Average GPA of Fall 2025 acceptances."""
    return one(
        """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE term ILIKE 'Fall 2025%%'
          AND status ILIKE 'Accept%%';
        """
    )


def q7():
    """Q7. # entries → JHU for Masters in Computer Science."""
    return one(
        """
        SELECT COUNT(*) FROM applicants
        WHERE llm_generated_university ILIKE '%%Johns Hopkins%%'
          AND llm_generated_program   ILIKE '%%Computer Science%%'
          AND (degree ILIKE '%%MS%%' OR degree ILIKE '%%Master%%');
        """
    )


def q8():
    """Q8. # acceptances (2025) → Georgetown PhD in CS."""
    return one(
        """
        SELECT COUNT(*) FROM applicants
        WHERE term ILIKE '%%2025%%'
          AND status ILIKE 'Accept%%'
          AND llm_generated_university ILIKE '%%Georgetown%%'
          AND llm_generated_program   ILIKE '%%Computer Science%%'
          AND (degree ILIKE '%%PhD%%' OR degree ILIKE '%%Doctor%%');
        """
    )

# ---------------------------------------------------------------------------
# Script runner
# ---------------------------------------------------------------------------

def run_all():
    """Run all queries and print results (for quick grading/demo)."""
    print("Q1 Fall 2025 count:", q1())
    print("Q2 % international:", q2())
    print("Q3 avgs:", j(q3()))
    print("Q4 avg GPA US Fall 2025:", q4())
    print("Q5 % accept Fall 2025:", q5())
    print("Q6 avg GPA accept Fall 2025:", q6())
    print("Q7 JHU MS CS:", q7())
    print("Q8 GT PhD CS accept 2025:", q8())


if __name__ == "__main__":
    run_all()