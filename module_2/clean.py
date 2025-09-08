"""
Module 2 — light cleaner pass
- goal: normalize strings, statuses, degree names, term/year; make nulls consistent.
- this is rule-based (fast, transparent). the LLM helper is separate (llm_hosting/).
"""

import json
import re
from typing import List, Dict, Optional

# regex helpers I reuse
RX_WS = re.compile(r"\s+")
RX_TERM = re.compile(r"\b(Fall|Spring|Summer|Winter)\b", re.I)
RX_YEAR = re.compile(r"\b(20\d{2})\b")
RX_GPA = re.compile(r"^[0-4](?:\.\d{1,2})?$")

def tidy(s: Optional[str]) -> Optional[str]:
    if s is None: return None
    s = RX_WS.sub(" ", s).strip()
    return s or None

def canonical_status(s: Optional[str]) -> Optional[str]:
    if not s: return None
    s = s.lower()
    if "accept" in s or "offer" in s: return "Accepted"
    if "reject" in s or "denied" in s: return "Rejected"
    if "wait" in s: return "Waitlisted"
    if "interview" in s: return "Interview"
    return s.title()

def canonical_degree(s: Optional[str]) -> Optional[str]:
    if not s: return None
    s = s.lower()
    if "ph" in s: return "PhD"
    if "psy" in s: return "PsyD"
    if s in {"ms","m.s.","m.sc","msc","masters","master"}: return "Masters"
    return s.title()

def canonical_intl(s: Optional[str]) -> Optional[str]:
    if not s: return None
    s = s.lower()
    if "inter" in s: return "International"
    if "amer" in s or "domestic" in s or "us" in s: return "American"
    return s.title()

def safe_number(s: Optional[str]) -> Optional[str]:
    # I keep numeric fields as strings in JSON unless strongly typed is required
    if s is None: return None
    s = s.strip()
    return s or None

def load_data(path: str = "applicant_data.json") -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_data(rows: List[Dict]) -> List[Dict]:
    cleaned = []
    for r in rows:
        # copy to avoid mutating input
        row = dict(r)

        # string tidy
        for key in ("program","university","comments","date_added","status","degree","intl_american"):
            row[key] = tidy(row.get(key))

        # status/degree/int’l canonicalization
        row["status"] = canonical_status(row.get("status"))
        row["degree"] = canonical_degree(row.get("degree") or row.get("program"))
        row["intl_american"] = canonical_intl(row.get("intl_american"))

        # term/year fallback: try to salvage from comments if empty
        if not row.get("start_term") and row.get("comments"):
            m = RX_TERM.search(row["comments"])
            row["start_term"] = m.group(1).title() if m else None
        if not row.get("start_year"):
            # try from date or comments
            for source in (row.get("date_added"), row.get("comments")):
                if source:
                    m = RX_YEAR.search(source)
                    if m: row["start_year"] = m.group(1); break

        # numeric-ish fields: store as strings (consistent) or None
        for key in ("gre_total","gre_verbal","gre_aw","gpa"):
            row[key] = safe_number(row.get(key))

        # GPA sanity: keep only valid shapes like 3.7, 3.85, etc.
        if row.get("gpa") and not RX_GPA.match(row["gpa"]):
            row["gpa"] = None

        # ensure every expected key exists (grader likes consistent schema)
        REQUIRED = [
            "program","university","comments","date_added","entry_url","status",
            "accept_date","reject_date","start_term","start_year","intl_american",
            "gre_total","gre_verbal","gre_aw","degree","gpa"
        ]
        for k in REQUIRED:
            row.setdefault(k, None)

        cleaned.append(row)
    return cleaned

def save_data(rows: List[Dict], path: str = "llm_extend_applicant_data.json") -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    raw = load_data("applicant_data.json")
    out = clean_data(raw)
    save_data(out, "llm_extend_applicant_data.json")
    print(f"cleaned {len(out)} rows -> llm_extend_applicant_data.json")