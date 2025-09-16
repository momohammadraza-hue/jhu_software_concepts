# -*- coding: utf-8 -*-
"""
Clean & normalize GradCafe data for Module 2 / 3.

This script accepts either:
- A JSON array file (e.g., applicant_data.json)
- A JSON Lines file (e.g., *.jsonl), one object per line

It emits:
- data/gradcafe_cleaned.csv : canonical CSV for Module 3
- data/clean_for_llm.jsonl  : minimal JSONL the LLM normalizer will read

Field policy (matches the professor’s table for Module 3):
    p_id (added later in SQL), program, comments, date_added, url,
    status, term, us_or_international, gpa, gre, gre_v, gre_aw,
    degree, llm_generated_program (optional merge later),
    llm_generated_university (optional merge later)

Design choices:
- Be tolerant of slightly different raw keys (e.g., url vs entry_url).
- Strip HTML-ish whitespace; empty strings become None.
- No LLM here—this just prepares clean CSV and the LLM input file.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional


# --------- utilities --------- #

def _clean(s: Optional[str]) -> Optional[str]:
    """Trim and collapse whitespace; return None for empty."""
    if s is None:
        return None
    s2 = " ".join(str(s).split()).strip()
    return s2 or None


def _num(s: Optional[str]) -> Optional[float]:
    """Parse a number if possible, else None."""
    if s is None:
        return None
    try:
        return float(str(s).strip())
    except Exception:
        return None


def _read_json_or_jsonl(path: Path) -> Iterator[Dict]:
    """Yield dict rows from JSON array (.json) or JSONL (.jsonl)."""
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if isinstance(obj, dict):
                    yield obj
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for obj in data:
                if isinstance(obj, dict):
                    yield obj


# --------- normalization --------- #

CSV_HEADERS = [
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
    # reserved for later merge (LLM step)
    "llm_generated_program",
    "llm_generated_university",
]


def to_csv_row(raw: Dict) -> Dict[str, Optional[str]]:
    """Map a raw dict into the canonical CSV schema."""
    # tolerate both url/entry_url; term/start_term; etc.
    url = raw.get("entry_url") or raw.get("url")
    term = raw.get("start_term") or raw.get("term")
    # “us_or_international” sometimes appears as “intl_american”
    us_intl = raw.get("us_or_international") or raw.get("intl_american")

    row = {
        "program": _clean(raw.get("program")),
        "comments": _clean(raw.get("comments")),
        "date_added": _clean(raw.get("date_added")),
        "url": _clean(url),
        "status": _clean(raw.get("status")),
        "term": _clean(term),
        "us_or_international": _clean(us_intl),
        "gpa": _num(raw.get("gpa")),
        "gre": _num(raw.get("gre_total") or raw.get("gre")),
        "gre_v": _num(raw.get("gre_verbal") or raw.get("gre_v")),
        "gre_aw": _num(raw.get("gre_aw")),
        "degree": _clean(raw.get("degree")),
        "llm_generated_program": None,
        "llm_generated_university": None,
    }
    return row


def to_llm_minimal(raw: Dict) -> Dict[str, Optional[str]]:
    """Minimal record the local LLM needs to standardize program/university."""
    return {
        "program": _clean(raw.get("program")),
        "university": _clean(raw.get("university")),
        "entry_url": _clean(raw.get("entry_url") or raw.get("url")),
        "date_added": _clean(raw.get("date_added")),
    }


# --------- I/O driver --------- #

def write_csv(out_csv: Path, rows: Iterable[Dict]) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        w.writeheader()
        w.writerows(rows)


def write_jsonl(out_jsonl: Path, rows: Iterable[Dict]) -> None:
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Normalize scraped GradCafe JSON/JSONL → CSV + LLM-prep JSONL."
    )
    ap.add_argument(
        "--src",
        required=True,
        help="Path to raw JSON (array) or JSONL produced by your scraper.",
    )
    ap.add_argument(
        "--out",
        default="data/gradcafe_cleaned.csv",
        help="CSV output path (default: data/gradcafe_cleaned.csv)",
    )
    ap.add_argument(
        "--llm_prep",
        default="data/clean_for_llm.jsonl",
        help="Minimal JSONL for the LLM normalizer (default: data/clean_for_llm.jsonl)",
    )
    args = ap.parse_args()

    src = Path(args.src)
    out_csv = Path(args.out)
    out_llm = Path(args.llm_prep)

    raw_iter = list(_read_json_or_jsonl(src))

    csv_rows = [to_csv_row(r) for r in raw_iter]
    write_csv(out_csv, csv_rows)

    # Reuse the same raw to create the LLM input (program/university only)
    llm_rows = [to_llm_minimal(r) for r in raw_iter]
    write_jsonl(out_llm, llm_rows)

    print(
        f"cleaned rows: {len(csv_rows)} → {out_csv}\n"
        f"llm-prep rows: {len(llm_rows)} → {out_llm}"
    )


if __name__ == "__main__":
    main()