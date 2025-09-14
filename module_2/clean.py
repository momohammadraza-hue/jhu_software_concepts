"""
Module 2 — Clean and normalize scraped GradCafe data.

Purpose:
    • Read the merged scrape output (JSONL or JSON).
    • Normalize dates, numeric fields, terms (Fall/Spring/etc.).
    • Map nationality labels to a small controlled set.
    • Optionally merge canonicalized fields from llm_extend_applicant_data.json.
    • Write a tidy CSV (data/gradcafe_cleaned.csv) for Module 3 loading.

Notes:
    • Only course-allowed libraries are used (stdlib).
    • If the LLM extension file is present, we copy its
      llm_generated_program / llm_generated_university columns in.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------------------------

from pathlib import Path
from typing import Iterable, Iterator, Optional, Dict, Any
import argparse
import csv
import json
import math
from datetime import datetime

# ---------------------------------------------------------------------------
# Defaults (override via CLI if needed)
# ---------------------------------------------------------------------------

# Default source: JSONL from scraper/merge. You can point to JSON instead.
DEFAULT_SRC = Path(__file__).parent / "applicant_data.jsonl"

# If present, provides canonicalized program/university fields.
DEFAULT_LLM = Path(__file__).parent / "llm_extend_applicant_data.json"

# Destination CSV used by Module 3 loader.
DEFAULT_OUT = Path(__file__).parent / "data" / "gradcafe_cleaned.csv"

# Ensure output folder exists.
DEFAULT_OUT.parent.mkdir(parents=True, exist_ok=True)

# Accepted date formats commonly seen on GradCafe (order matters).
DATE_FORMATS: tuple[str, ...] = (
    "%Y-%m-%d",      # ISO: 2025-01-31
    "%m/%d/%Y",      # US: 01/31/2025
    "%d-%m-%Y",      # EU-ish: 31-01-2025
    "%b %d, %Y",     # Long: Jan 31, 2025
)

# ---------------------------------------------------------------------------
# Helper functions (pure, testable)
# ---------------------------------------------------------------------------


def to_float(x: Any) -> Optional[float]:
    """
    Convert common numeric strings to float; return None on failure.

    Handles:
        • Empty / sentinel strings ("", NA, N/A, None, null).
        • Numbers with commas / currency symbols.
        • Existing ints / floats (filters out NaN).

    Args:
        x: Input value from a record.

    Returns:
        float or None when conversion is not possible.
    """
    if x is None:
        return None
    if isinstance(x, (int, float)):
        # Guard against NaN, which compares unequal to itself.
        if isinstance(x, float) and math.isnan(x):
            return None
        return float(x)

    s = str(x).strip()
    if s in {"", "NA", "N/A", "None", "null", "Null"}:
        return None
    s = s.replace(",", "").replace("$", "")
    try:
        return float(s)
    except Exception:
        return None


def to_date(x: Any) -> Optional[str]:
    """
    Normalize a variety of date strings to ISO (YYYY-MM-DD).

    Tries the DATE_FORMATS in order and returns None if none match.

    Args:
        x: Input date-like value.

    Returns:
        ISO date string or None.
    """
    if not x:
        return None
    s = str(x).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            # Try next format.
            continue
    return None


def norm_term(s: Any) -> Optional[str]:
    """
    Normalize term to a canonical label in Title Case.

    Canonical outputs:
        "Fall", "Spring", "Summer", "Winter"
    """
    if not s:
        return None
    t = str(s).strip().lower()
    if t in {"fall", "fa", "f"}:
        return "Fall"
    if t in {"spring", "sp", "spr"}:
        return "Spring"
    if t in {"summer", "su", "sum"}:
        return "Summer"
    if t in {"winter", "wi", "win"}:
        return "Winter"
    return t.title()


def build_term(start_term: Any,
               start_year: Any,
               accept_date: Any = None,
               reject_date: Any = None) -> Optional[str]:
    """
    Build a friendly "Term Year" label from multiple hints.

    Priority order:
        1) start_term + start_year (best)
        2) whichever of term/year is present
        3) infer year from accept/reject decision date(s)

    Returns:
        "Fall 2025", "Spring", "2024", or None if no clue is available.
    """
    term = norm_term(start_term)
    year_str = str(start_year).strip() if start_year not in (None, "", "nan") else ""

    # Term and year both present and valid.
    if term and year_str.isdigit():
        return f"{term} {year_str}"

    # Only term present.
    if term and not year_str:
        return term

    # Only year present.
    if year_str.isdigit():
        return year_str

    # Fallback: infer year from decision dates.
    ds = to_date(accept_date) or to_date(reject_date)
    if ds:
        return str(datetime.fromisoformat(ds).year)

    return None


def norm_nat(v: Any) -> Optional[str]:
    """
    Map free-text nationality label to a small set.

    Canonical outputs:
        "American", "International", "Other", or None when unknown.
    """
    if not v:
        return None
    s = str(v).strip().lower()
    if "american" in s or s in {"us", "usa", "u.s.", "u.s.a.", "american"}:
        return "American"
    if "intern" in s or s in {"int", "intl", "international"}:
        return "International"
    if "other" in s:
        return "Other"
    return None


def load_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    """
    Stream records from a JSON Lines file.

    Yields one dict per line; skips blank lines.
    """
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_json_array(path: Path) -> list[Dict[str, Any]]:
    """
    Load a JSON file that contains a list of objects.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def iter_source_rows(src: Path) -> Iterable[Dict[str, Any]]:
    """
    Iterate records from a source file that may be JSONL or JSON.

    This allows calling the cleaner with either:
        • applicant_data.jsonl  (line-delimited)
        • applicant_data.json   (array of dicts)
    """
    if src.suffix.lower() == ".jsonl":
        yield from load_jsonl(src)
    elif src.suffix.lower() == ".json":
        for rec in load_json_array(src):
            yield rec
    else:
        raise ValueError(f"Unsupported source extension: {src.suffix}")

# ---------------------------------------------------------------------------
# Core cleaning
# ---------------------------------------------------------------------------


def clean_data(src: Path = DEFAULT_SRC,
               out_csv: Path = DEFAULT_OUT,
               llm_path: Optional[Path] = DEFAULT_LLM) -> int:
    """
    Transform scraped rows into a clean CSV for Module 3.

    Behavior:
        • Normalizes date fields into one 'date_added' column.
        • Produces a single 'term' column (e.g., "Fall 2025").
        • Converts GPA/GRE values to floats, or None when not present.
        • Maps nationality labels to 'American'/'International'/'Other'.
        • Copies llm_* fields from llm_extend_applicant_data.json if present.

    Args:
        src: Source data path (JSONL or JSON array).
        out_csv: Destination CSV path.
        llm_path: Optional path to llm_extend_applicant_data.json. If present
                  and aligned (same order/length), llm columns are taken from it.

    Returns:
        Number of rows written to CSV.
    """
    # Attempt to load LLM-extended rows (same order/length as source).
    llm_rows: Optional[list[Dict[str, Any]]] = None
    if llm_path and llm_path.exists():
        try:
            llm_rows = load_json_array(llm_path)
        except Exception:
            # If it is malformed, we silently ignore and fall back to raw fields.
            llm_rows = None

    rows_out: list[Dict[str, Any]] = []

    # Enumerate records for a stable synthetic primary key (p_id).
    for i, r in enumerate(iter_source_rows(src), start=1):
        # Build a friendly term string from hints.
        term = build_term(
            r.get("start_term"),
            r.get("start_year"),
            r.get("accept_date"),
            r.get("reject_date"),
        )

        # Default llm_* values come from raw fields; override if LLM file exists.
        llm_prog = r.get("program")
        llm_uni = r.get("university")
        if llm_rows and 0 <= i - 1 < len(llm_rows):
            lp = llm_rows[i - 1].get("llm_generated_program")
            lu = llm_rows[i - 1].get("llm_generated_university")
            llm_prog = lp or llm_prog
            llm_uni = lu or llm_uni

        # Build a single, normalized output row.
        rows_out.append(
            {
                "p_id": i,  # Synthetic, stable id for this export.
                "program": r.get("program"),
                "comments": r.get("comments"),
                "date_added": to_date(
                    r.get("date_added")
                    or r.get("accept_date")
                    or r.get("reject_date")
                ),
                "url": r.get("entry_url"),
                "status": r.get("status"),
                "term": term,
                "us_or_international": norm_nat(r.get("intl_american")),
                "gpa": to_float(r.get("gpa")),
                "gre": to_float(r.get("gre_total")),
                "gre_v": to_float(r.get("gre_verbal")),
                "gre_aw": to_float(r.get("gre_aw")),
                "degree": r.get("degree") or None,
                "llm_generated_program": llm_prog,
                "llm_generated_university": llm_uni,
            }
        )

    # Fixed CSV schema expected by Module 3 loader.
    cols = [
        "p_id",
        "program",
        "comments",
        "date_added",
        "url",
        "status",
        "term",
        "us_or_international",
        "gpa",
        "gre",
        "gre_v",
        "gre_aw",
        "degree",
        "llm_generated_program",
        "llm_generated_university",
    ]

    # Write CSV with header + all rows.
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"Wrote {len(rows_out)} rows → {out_csv.resolve()}")
    return len(rows_out)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the cleaner.

    You can pass a JSONL/JSON source, an alternative output CSV path,
    and an optional llm_extend_applicant_data.json to enrich llm_* columns.
    """
    parser = argparse.ArgumentParser(
        description="Clean scraped GradCafe data and write a CSV."
    )
    parser.add_argument(
        "--src",
        type=Path,
        default=DEFAULT_SRC,
        help="Source file: applicant_data.jsonl (default) or applicant_data.json.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Destination CSV path (default: data/gradcafe_cleaned.csv).",
    )
    parser.add_argument(
        "--llm",
        type=Path,
        default=DEFAULT_LLM,
        help="Optional path to llm_extend_applicant_data.json.",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for script usage."""
    args = _parse_args()
    clean_data(src=args.src, out_csv=args.out, llm_path=args.llm)


if __name__ == "__main__":
    main()