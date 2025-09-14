"""
Module 2 — Data Validator

This script validates scraped and cleaned GradCafe data.

Checks performed:
  • Row count (expect ≥30,000 for the final dataset, but smaller is fine during dev).
  • Presence of all required keys (sampled on first 1000 rows).
  • Detection of any lingering HTML fragments in text fields
    (scanned on first 2000 rows).
"""

from __future__ import annotations

import json
import os
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Expected keys from scraper/cleaner. These should appear in every record.
REQUIRED = {
    "program",
    "university",
    "comments",
    "date_added",
    "entry_url",
    "status",
    "accept_date",
    "reject_date",
    "start_term",
    "start_year",
    "intl_american",
    "gre_total",
    "gre_verbal",
    "gre_aw",
    "degree",
    "gpa",
}

# ---------------------------------------------------------------------------
# Core validation function
# ---------------------------------------------------------------------------

def check(path: str) -> None:
    """
    Validate a JSON file of applicant rows.

    Args:
        path: Path to JSON file to validate (expects a list of dicts).

    Prints:
        - Row count.
        - Missing keys across a 1000-row sample.
        - Count of rows with potential HTML fragments
          across a 2000-row sample.
    """
    # Ensure the file exists before attempting to load.
    if not os.path.exists(path):
        print(f"[!] {path} not found")
        return

    # Load the data from JSON into memory.
    with open(path, "r", encoding="utf-8") as f:
        data: list[dict[str, Any]] = json.load(f)

    # Report the number of rows.
    print(f"[{path}] rows: {len(data)}")

    # -----------------------------------------------------------------------
    # Check for missing keys in a sample of rows.
    # -----------------------------------------------------------------------
    missing: set[str] = set()
    for r in data[:1000]:
        missing |= (REQUIRED - set(r))
    if missing:
        print("Missing keys in sample:", sorted(missing))

    # -----------------------------------------------------------------------
    # Scan for potential HTML fragments in text fields.
    # -----------------------------------------------------------------------
    htmly = 0
    for r in data[:2000]:
        for k in ("program", "university", "comments"):
            v = r.get(k)
            if isinstance(v, str) and "<" in v and ">" in v:
                htmly += 1
                break
    print("Potential HTML fragments (first 2000 rows):", htmly)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Validate raw scraped data.
    check("applicant_data.json")

    # Validate canonicalized version (if present).
    check("llm_extend_applicant_data.json")