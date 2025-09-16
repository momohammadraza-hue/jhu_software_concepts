# module_3_new/load_data.py
"""Load cleaned GradCafe CSV into PostgreSQL (psycopg v3).

Expected CSV headers (from module_2_new/clean.py):
  program, comments, date_added, url, status, term, us_or_international,
  gpa, gre, gre_v, gre_aw, degree,
  llm_generated_program, llm_generated_university

Optional:
  Backfill LLM-normalized fields from module_2_new/data/llm_extended.jsonl
  using join key (url|entry_url, date_added).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import psycopg


DDL = """
CREATE TABLE IF NOT EXISTS applicants (
  p_id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  program           TEXT,
  university        TEXT,                -- mirror normalized university for convenience
  comments          TEXT,
  date_added        DATE,
  url               TEXT,
  status            TEXT,
  term              TEXT,
  us_or_international TEXT,
  gpa               DOUBLE PRECISION,
  gre               DOUBLE PRECISION,
  gre_v             DOUBLE PRECISION,
  gre_aw            DOUBLE PRECISION,
  degree            TEXT,
  program_norm      TEXT,                -- llm_generated_program
  university_norm   TEXT                 -- llm_generated_university
);
"""

INSERT_SQL = """
INSERT INTO applicants
(program, university, comments, date_added, url, status, term, us_or_international,
 gpa, gre, gre_v, gre_aw, degree, program_norm, university_norm)
VALUES
(%(program)s, %(university)s, %(comments)s, %(date_added)s, %(url)s, %(status)s,
 %(term)s, %(us_or_international)s, %(gpa)s, %(gre)s, %(gre_v)s, %(gre_aw)s,
 %(degree)s, %(program_norm)s, %(university_norm)s)
"""


def parse_date(s: Optional[str]) -> Optional[dt.date]:
    """Return a date for common formats or None."""
    if not s:
        return None
    txt = s.strip()
    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(txt, fmt).date()
        except ValueError:
            continue
    return None


def parse_num(s: Optional[str]) -> Optional[float]:
    """Parse float-like strings; return None on failure/empty."""
    if s in (None, ""):
        return None
    try:
        return float(str(s).strip())
    except Exception:
        return None


def read_llm_index(
    llm_jsonl: Optional[Path],
) -> Dict[Tuple[str, str], Tuple[Optional[str], Optional[str]]]:
    """Build an index (url/date_added) → (program_norm, university_norm).

    If the file path is None or missing, returns an empty dict.
    """
    idx: Dict[Tuple[str, str], Tuple[Optional[str], Optional[str]]] = {}
    if not llm_jsonl or not llm_jsonl.exists():
        return idx

    with llm_jsonl.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            url = obj.get("entry_url") or obj.get("url") or ""
            date_added = obj.get("date_added") or ""
            if not url:
                continue
            pn = obj.get("llm-generated-program") or obj.get("llm_generated_program")
            un = obj.get("llm-generated-university") or obj.get(
                "llm_generated_university"
            )
            idx[(url, date_added)] = (pn, un)
    return idx


def csv_iter(path: Path) -> Iterable[dict]:
    """Yield dict rows from a CSV file."""
    with path.open(newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            yield row


def _clean_text(s: Optional[str]) -> Optional[str]:
    """Trim whitespace; return None for empty."""
    if s is None:
        return None
    out = s.strip()
    return out or None


def map_row(
    rec: dict,
    llm_idx: Dict[Tuple[str, str], Tuple[Optional[str], Optional[str]]],
) -> Dict[str, object]:
    """Map one CSV row into the DB insert dict, backfilling LLM fields if needed."""
    url = _clean_text(rec.get("url"))
    date_added_raw = rec.get("date_added") or ""

    out: Dict[str, object] = {
        "program": _clean_text(rec.get("program")),
        "university": None,  # will mirror university_norm below
        "comments": _clean_text(rec.get("comments")),
        "date_added": parse_date(date_added_raw),
        "url": url,
        "status": _clean_text(rec.get("status")),
        "term": _clean_text(rec.get("term")),
        "us_or_international": _clean_text(rec.get("us_or_international")),
        "gpa": parse_num(rec.get("gpa")),
        "gre": parse_num(rec.get("gre")),
        "gre_v": parse_num(rec.get("gre_v")),
        "gre_aw": parse_num(rec.get("gre_aw")),
        "degree": _clean_text(rec.get("degree")),
        "program_norm": _clean_text(rec.get("llm_generated_program")),
        "university_norm": _clean_text(rec.get("llm_generated_university")),
    }

    # Backfill normalized fields from JSONL if missing.
    if (not out["program_norm"] or not out["university_norm"]) and url:
        key = (url, date_added_raw)
        pn_un = llm_idx.get(key)
        if pn_un:
            pn, un = pn_un
            out["program_norm"] = out["program_norm"] or (pn or None)
            out["university_norm"] = out["university_norm"] or (un or None)

    # Mirror normalized university into the plain 'university' column for convenience.
    out["university"] = out["university_norm"]
    return out


def load_csv_into_db(
    csv_path: Path,
    dsn: str,
    llm_jsonl: Optional[Path] = None,
    truncate: bool = False,
    batch_size: int = 1000,
) -> int:
    """Load CSV (and optional LLM JSONL) into PostgreSQL, returning rows loaded."""
    llm_idx = read_llm_index(llm_jsonl) if llm_jsonl else {}

    loaded = 0
    with psycopg.connect(dsn, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            if truncate:
                cur.execute("TRUNCATE TABLE applicants;")

            batch: List[Dict[str, object]] = []
            for rec in csv_iter(csv_path):
                batch.append(map_row(rec, llm_idx))
                if len(batch) >= batch_size:
                    cur.executemany(INSERT_SQL, batch)
                    loaded += len(batch)
                    batch.clear()

            if batch:
                cur.executemany(INSERT_SQL, batch)
                loaded += len(batch)

        conn.commit()

    return loaded


def main() -> None:
    """CLI entrypoint."""
    ap = argparse.ArgumentParser(
        description="Load Module 2 CSV into PostgreSQL (psycopg v3)."
    )
    ap.add_argument(
        "--csv",
        required=True,
        help="Path to module_2_new/data/gradcafe_cleaned.csv",
    )
    ap.add_argument(
        "--llm-jsonl",
        help="Optional path to module_2_new/data/llm_extended.jsonl",
    )
    ap.add_argument(
        "--dsn",
        default="postgresql://localhost/gradcafe",
        help="Postgres DSN, e.g. postgresql://user:pass@localhost:5432/gradcafe",
    )
    ap.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate table before load",
    )
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    llm_jsonl_path = Path(args.llm_jsonl) if args.llm_jsonl else None

    count = load_csv_into_db(
        csv_path=csv_path,
        dsn=args.dsn,
        llm_jsonl=llm_jsonl_path,
        truncate=bool(args.truncate),
    )
    print(f"loaded rows: {count}")


if __name__ == "__main__":
    main()