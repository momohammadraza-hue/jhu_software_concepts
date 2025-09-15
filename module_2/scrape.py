"""
Module 2 — raw web scrape to JSON (table-aware + resumable)

Libraries (per course):
  - urllib3
  - bs4 (BeautifulSoup)
  - stdlib (argparse, json, time, re, os, typing)

What this does:
  1) Parse the results TABLE by header names when present.
  2) If no table, fall back to a card/div layout with broad selectors.
  3) Stream results to JSONL (resumable) and also write a merged JSON array.
  4) Simple de-dup across runs keyed by (entry_url, program, university).
  5) Show a running total of rows appended to the JSONL stream.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import argparse
import json
import os
import re
import time

import urllib3
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry

# Optional TLS bundle (helps on some macOS venv setups).
try:
    import certifi  # not a scraping helper; just a CA bundle
    _CA_BUNDLE = certifi.where()
except Exception:
    _CA_BUNDLE = None

# ----------------------------- schema / regex ------------------------------

REQUIRED_KEYS = [
    "program", "university", "comments", "date_added", "entry_url", "status",
    "accept_date", "reject_date", "start_term", "start_year", "intl_american",
    "gre_total", "gre_verbal", "gre_aw", "degree", "gpa",
]

RX_GPA = re.compile(r"\bGPA[:\s]*([0-4](?:\.\d{1,2})?)\b", re.I)
RX_GRE_T = re.compile(r"\bGRE(?:\s*Total)?[:\s]*([12]\d{2,3})\b", re.I)
RX_GRE_V = re.compile(r"\bGRE-?V(?:erbal)?[:\s]*([12]\d{2})\b", re.I)
RX_GRE_AW = re.compile(r"\bGRE-?AW[:\s]*([0-6](?:\.\d)?)\b", re.I)
RX_TERM = re.compile(r"\b(Fall|Spring|Summer|Winter)\b", re.I)
RX_YEAR = re.compile(r"\b(20\d{2})\b")
RX_STATUS = re.compile(r"\b(accepted|rejected|waitlisted|interview|offer)\b", re.I)
RX_INTL = re.compile(r"\b(international|american|domestic|us citizen)\b", re.I)
RX_DEGREE = re.compile(r"\b(Ph\.?D|PhD|Masters|MS|M\.S\.|MSc|PsyD|MEng)\b", re.I)
RX_DATE = re.compile(
    r"\b(?:\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|[A-Z][a-z]{2}\s+\d{1,2},\s*\d{4})\b"
)

# ----------------------------- tiny utils ----------------------------------


def _txt(el) -> str:
    """Return normalized text from a BeautifulSoup element."""
    return el.get_text(" ", strip=True) if el else ""


def _first(rx: re.Pattern, s: str) -> Optional[str]:
    """Return first regex group match or None."""
    m = rx.search(s or "")
    return m.group(1) if m else None


def _norm_status(s: Optional[str]) -> Optional[str]:
    """Normalize status strings to a small set."""
    if not s:
        return None
    s = s.lower()
    if "accept" in s or "offer" in s:
        return "Accepted"
    if "reject" in s or "denied" in s:
        return "Rejected"
    if "wait" in s:
        return "Waitlisted"
    if "interview" in s:
        return "Interview"
    return s.title()


def _norm_degree(s: Optional[str]) -> Optional[str]:
    """Normalize degree labels (PhD / Masters / PsyD)."""
    if not s:
        return None
    s = s.lower()
    if "ph" in s:
        return "PhD"
    if "psy" in s:
        return "PsyD"
    if s in {"ms", "m.s.", "m.sc", "msc", "masters", "master"}:
        return "Masters"
    return s.title()


def _norm_intl(s: Optional[str]) -> Optional[str]:
    """Map variations to 'International' or 'American' when possible."""
    if not s:
        return None
    s = s.lower()
    if "inter" in s:
        return "International"
    if "amer" in s or "domestic" in s or "us" in s:
        return "American"
    return s.title()


def _blank(url: str) -> Dict[str, Optional[str]]:
    """Return a dict containing required keys with default None values."""
    return {
        "program": None, "university": None, "comments": None, "date_added": None,
        "entry_url": url, "status": None, "accept_date": None, "reject_date": None,
        "start_term": None, "start_year": None, "intl_american": None,
        "gre_total": None, "gre_verbal": None, "gre_aw": None, "degree": None, "gpa": None
    }


def make_http() -> urllib3.PoolManager:
    """Create a PoolManager with polite retries (and optional certifi CAs)."""
    kwargs = dict(retries=Retry(total=3, backoff_factor=0.5, raise_on_status=False))
    if _CA_BUNDLE:
        kwargs.update(dict(cert_reqs="CERT_REQUIRED", ca_certs=_CA_BUNDLE))
    return urllib3.PoolManager(**kwargs)


def _count_jsonl_lines(path: str) -> int:
    """Fast count of records already in the JSONL stream (running total)."""
    if not os.path.exists(path):
        return 0
    n = 0
    with open(path, "r", encoding="utf-8") as f:
        for _ in f:
            n += 1
    return n


# ----------------------------- table parsing -------------------------------


def _find_results_table(soup: BeautifulSoup):
    """
    Find a table whose headers look like: School | Program | Added On | Decision.
    Return (table, header_idx_map) or (None, None).
    """
    for table in soup.select("table"):
        heads = [_txt(th).lower() for th in table.select("thead th")]
        if not heads:
            first_row = table.select_one("tbody tr")
            if first_row:
                heads = [_txt(th).lower()
                         for th in first_row.find_all(["th", "td"])]
        if not heads:
            continue

        idx = {}
        for i, h in enumerate(heads):
            if "school" in h or "university" in h:
                idx["university"] = i
            if "program" in h:
                idx["program"] = i
            if "added" in h or "date" in h:
                idx["date_added"] = i
            if "decision" in h or "status" in h:
                idx["status"] = i
            if "comment" in h or "note" in h:
                idx["comments"] = i

        if ("university" in idx and "program" in idx) or ("status" in idx):
            return table, idx
    return None, None


def _rows_from_table(table, idx_map, page_url: str) -> List[Dict[str, Optional[str]]]:
    """Extract rows from a <table> using an index map of important columns."""
    out: List[Dict[str, Optional[str]]] = []
    body = table.select_one("tbody") or table
    for tr in body.select("tr"):
        cells = tr.find_all(["td", "th"])
        if not cells or len(cells) < 2:
            continue
        if any(c.name == "th" for c in cells):
            continue

        row = _blank(page_url)

        def cell(i: Optional[int]) -> str:
            return _txt(cells[i]) if i is not None and i < len(cells) else ""

        uni = cell(idx_map.get("university"))
        prog = cell(idx_map.get("program"))
        dat = cell(idx_map.get("date_added"))
        sta = cell(idx_map.get("status"))
        com = cell(idx_map.get("comments"))

        row["university"] = uni or None
        row["program"] = prog or None
        row["date_added"] = dat or _first(RX_DATE, " ".join([uni, prog, com, sta]))
        row["status"] = _norm_status(sta) or _norm_status(_first(RX_STATUS, sta))
        row["comments"] = com or None
        row["degree"] = _norm_degree(_first(RX_DEGREE, " ".join([prog, com])))
        row["start_term"] = _first(RX_TERM, com)
        row["start_year"] = _first(RX_YEAR, " ".join([dat, com]))
        row["intl_american"] = _norm_intl(_first(RX_INTL, com))
        row["gpa"] = _first(RX_GPA, com)
        row["gre_total"] = _first(RX_GRE_T, com)
        row["gre_verbal"] = _first(RX_GRE_V, com)
        row["gre_aw"] = _first(RX_GRE_AW, com)

        for k, v in list(row.items()):
            if isinstance(v, str):
                v = v.strip()
                row[k] = v if v else None

        if row["university"] or row["program"] or row["status"]:
            out.append(row)
    return out


# ----------------------------- card fallback -------------------------------


def _rows_from_cards(soup: BeautifulSoup, page_url: str) -> List[Dict[str, Optional[str]]]:
    """
    Broadened selectors so we capture result cards/rows in non-table layouts.
    """
    blocks = (
        soup.select("div[role='row']") or
        soup.select("article") or
        soup.select("ul li") or
        soup.select("div.tw-flex.tw-items-center, div.tw-inline-flex.tw-items-center") or
        soup.select(".result-row, .c-result, .result, article, .search-result, .post, tr.result") or
        soup.select('div[class*="result"], section[class*="result"]') or
        []
    )

    rows: List[Dict[str, Optional[str]]] = []
    for b in blocks:
        row = _blank(page_url)

        uni_el = b.select_one(".university, .institution, .c-institution, .inst, "
                              ".td-institution")
        prog_el = b.select_one(".program, .c-program, .td-program")
        comm_el = b.select_one(".comments, .c-comments, .td-comments")
        date_el = b.select_one(".date, .c-date, time, .td-date")
        stat_el = b.select_one(".status, .c-decision, .decision, .td-decision")

        blob = _txt(b)

        row["university"] = _txt(uni_el) or None
        row["program"] = _txt(prog_el) or None
        row["comments"] = _txt(comm_el) or None
        row["date_added"] = _txt(date_el) or _first(RX_DATE, blob)
        row["status"] = _norm_status(_txt(stat_el)) or _norm_status(
            _first(RX_STATUS, blob)
        )

        if not row["university"]:
            parts = [p.strip() for p in re.split(r"[•|–|-]{1,}| {2,}", blob) if p.strip()]
            row["university"] = parts[0] if parts else None

        row["gpa"] = _first(RX_GPA, blob)
        row["gre_total"] = _first(RX_GRE_T, blob)
        row["gre_verbal"] = _first(RX_GRE_V, blob)
        row["gre_aw"] = _first(RX_GRE_AW, blob)
        row["start_term"] = _first(RX_TERM, blob)
        row["start_year"] = _first(RX_YEAR, blob)
        row["intl_american"] = _norm_intl(_first(RX_INTL, blob))
        if not row["degree"]:
            row["degree"] = _norm_degree(_first(RX_DEGREE, blob) or row["program"])

        for k, v in list(row.items()):
            if isinstance(v, str):
                v = v.strip()
                row[k] = v if v else None

        if row["university"] or row["program"] or row["status"]:
            rows.append(row)

    return rows


# ----------------------------- one page ------------------------------------


def scrape_page(http: urllib3.PoolManager, url: str) -> List[Dict[str, Optional[str]]]:
    """Fetch one search page and return extracted rows."""
    r = http.request("GET", url)
    if r.status != 200:
        return []
    soup = BeautifulSoup(r.data, "html.parser")
    table, idx = _find_results_table(soup)
    if table:
        return _rows_from_table(table, idx, url)
    return _rows_from_cards(soup, url)


# ----------------------------- merge/save ----------------------------------


def save_data(rows: List[Dict[str, Optional[str]]], path: str = "applicant_data.json") -> None:
    """Write a JSON array with the required schema keys present."""
    for r in rows:
        for k in REQUIRED_KEYS:
            r.setdefault(k, None)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def write_jsonl(rows, path="applicant_data.jsonl") -> None:
    """Append streaming JSONL lines (resumable)."""
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def dedup_rows(rows, seen):
    """Simple de-dup key: (entry_url, program, university)."""
    out = []
    for r in rows:
        key = (r.get("entry_url"), r.get("program"), r.get("university"))
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


# ----------------------------- CLI / main ----------------------------------


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="GradCafe scraper (Module 2).")
    ap.add_argument("--q", default="computer science",
                    help="search query (e.g., 'computer science')")
    ap.add_argument("--pages", type=int, default=2,
                    help="number of pages to fetch")
    ap.add_argument("--start", type=int, default=1,
                    help="start page (resume)")
    ap.add_argument("--delay", type=float, default=0.8,
                    help="sleep between pages (seconds)")
    ap.add_argument("--out", default="applicant_data.jsonl",
                    help="streaming JSONL file")
    ap.add_argument("--final", default="applicant_data.json",
                    help="merged JSON array")
    ap.add_argument("--debug", action="store_true",
                    help="print rows found per page")
    args = ap.parse_args()

    # Build URL template from the query (space → plus).
    from urllib.parse import quote_plus
    BASE = f"https://www.thegradcafe.com/survey/?q={quote_plus(args.q)}&page={{page}}"

    http = make_http()
    seen = set()

    # Seed de-dup from existing JSONL (safe resume).
    if os.path.exists(args.out):
        with open(args.out, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    key = (r.get("entry_url"), r.get("program"), r.get("university"))
                    seen.add(key)
                except Exception:
                    pass

    # Running total starts with whatever is already in the JSONL stream.
    running_total = _count_jsonl_lines(args.out)

    added = 0
    for p in range(args.start, args.start + args.pages):
        url = BASE.format(page=p)
        page_rows = scrape_page(http, url)
        if args.debug:
            print(f"q='{args.q}' page={p} -> raw_rows={len(page_rows)}")

        page_rows = dedup_rows(page_rows, seen)

        if page_rows:
            write_jsonl(page_rows, args.out)
            added += len(page_rows)
            running_total += len(page_rows)

        # Progress line after each page (always prints; helpful for long runs).
        print(
            f"q='{args.q}' page={p} -> added {len(page_rows)} "
            f"(running total: {running_total})"
        )

        time.sleep(args.delay)  # be polite

    # Merge JSONL → JSON array for cleaner/validator.
    merged = []
    if os.path.exists(args.out):
        with open(args.out, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    merged.append(json.loads(line))
                except Exception:
                    pass

    save_data(merged, args.final)
    print(f"wrote {len(merged)} rows to {args.final} (added {added} new this run)")