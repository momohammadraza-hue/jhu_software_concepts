"""
Module 2 — raw web scrape to JSON (table-aware)
- urllib3 + bs4 only (week-2 rules)
- Detects the results TABLE by headers (School, Program, Added On, Decision)
  and extracts rows. Falls back to div/card parsing if table not present.
"""

import json, time, re
from typing import List, Dict, Optional
import urllib3
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry

try:
    import certifi
    _CA_BUNDLE = certifi.where()
except Exception:
    _CA_BUNDLE = None

BASE = "https://www.thegradcafe.com/survey/index.php?q=computer+science&page={page}"

REQUIRED_KEYS = [
    "program","university","comments","date_added","entry_url","status",
    "accept_date","reject_date","start_term","start_year","intl_american",
    "gre_total","gre_verbal","gre_aw","degree","gpa"
]

RX_GPA     = re.compile(r"\bGPA[:\s]*([0-4](?:\.\d{1,2})?)\b", re.I)
RX_GRE_T   = re.compile(r"\bGRE(?:\s*Total)?[:\s]*([12]\d{2,3})\b", re.I)
RX_GRE_V   = re.compile(r"\bGRE-?V(?:erbal)?[:\s]*([12]\d{2})\b", re.I)
RX_GRE_AW  = re.compile(r"\bGRE-?AW[:\s]*([0-6](?:\.\d)?)\b", re.I)
RX_TERM    = re.compile(r"\b(Fall|Spring|Summer|Winter)\b", re.I)
RX_YEAR    = re.compile(r"\b(20\d{2})\b")
RX_STATUS  = re.compile(r"\b(accepted|rejected|waitlisted|interview|offer)\b", re.I)
RX_INTL    = re.compile(r"\b(international|american|domestic|us citizen)\b", re.I)
RX_DEGREE  = re.compile(r"\b(Ph\.?D|PhD|Masters|MS|M\.S\.|MSc|PsyD|MEng)\b", re.I)
RX_DATE    = re.compile(r"\b(?:\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|[A-Z][a-z]{2}\s+\d{1,2},\s*\d{4})\b")

def _txt(el) -> str:
    return el.get_text(" ", strip=True) if el else ""

def _first(rx: re.Pattern, s: str) -> Optional[str]:
    m = rx.search(s or ""); return m.group(1) if m else None

def _norm_status(s: Optional[str]) -> Optional[str]:
    if not s: return None
    s=s.lower()
    if "accept" in s or "offer" in s:  return "Accepted"
    if "reject" in s or "denied" in s: return "Rejected"
    if "wait" in s:                    return "Waitlisted"
    if "interview" in s:               return "Interview"
    return s.title()

def _norm_degree(s: Optional[str]) -> Optional[str]:
    if not s: return None
    s=s.lower()
    if "ph" in s: return "PhD"
    if "psy" in s: return "PsyD"
    if s in {"ms","m.s.","m.sc","msc","masters","master"}: return "Masters"
    return s.title()

def _norm_intl(s: Optional[str]) -> Optional[str]:
    if not s: return None
    s=s.lower()
    if "inter" in s: return "International"
    if "amer" in s or "domestic" in s or "us" in s: return "American"
    return s.title()

def _blank(url: str) -> Dict[str, Optional[str]]:
    return {
        "program": None, "university": None, "comments": None, "date_added": None,
        "entry_url": url, "status": None, "accept_date": None, "reject_date": None,
        "start_term": None, "start_year": None, "intl_american": None,
        "gre_total": None, "gre_verbal": None, "gre_aw": None, "degree": None, "gpa": None
    }

def make_http() -> urllib3.PoolManager:
    if _CA_BUNDLE:
        return urllib3.PoolManager(
            cert_reqs="CERT_REQUIRED", ca_certs=_CA_BUNDLE,
            retries=Retry(total=3, backoff_factor=0.5, raise_on_status=False)
        )
    return urllib3.PoolManager(retries=Retry(total=3, backoff_factor=0.5, raise_on_status=False))

# ---------- TABLE PARSER ----------

def _find_results_table(soup: BeautifulSoup):
    """
    Find the table that has headers like: School | Program | Added On | Decision
    Returns (table, header_index_map) or (None, None)
    """
    for table in soup.select("table"):
        # get header texts
        heads = [ _txt(th).lower() for th in table.select("thead th") ]
        if not heads:
            # sometimes headers are in first row of tbody
            first_row = table.select_one("tbody tr")
            if first_row:
                heads = [ _txt(th).lower() for th in first_row.find_all(["th","td"]) ]
        if not heads: 
            continue

        # normalize and map to indexes
        idx = {}
        for i,h in enumerate(heads):
            if "school" in h or "university" in h: idx["university"]=i
            if "program" in h:                      idx["program"]=i
            if "added" in h or "date" in h:        idx["date_added"]=i
            if "decision" in h or "status" in h:   idx["status"]=i
            if "comment" in h or "note" in h:      idx["comments"]=i

        # we at least need university + program OR status to call it a results table
        if ("university" in idx and "program" in idx) or ("status" in idx):
            return table, idx
    return None, None

def _rows_from_table(table, idx_map, page_url: str) -> List[Dict[str, Optional[str]]]:
    out = []
    body = table.select_one("tbody") or table
    for tr in body.select("tr"):
        cells = tr.find_all(["td","th"])
        if not cells or len(cells) < 2: 
            continue
        # skip header-like rows
        if any(c.name=="th" for c in cells): 
            continue

        row = _blank(page_url)
        def cell(i): 
            return _txt(cells[i]) if i is not None and i < len(cells) else ""

        uni = cell(idx_map.get("university"))
        prog = cell(idx_map.get("program"))
        dat  = cell(idx_map.get("date_added"))
        sta  = cell(idx_map.get("status"))
        com  = cell(idx_map.get("comments"))

        row["university"]  = uni or None
        row["program"]     = prog or None
        row["date_added"]  = dat or _first(RX_DATE, " ".join([uni,prog,com,sta]))
        row["status"]      = _norm_status(sta) or _norm_status(_first(RX_STATUS, sta))
        row["comments"]    = com or None
        row["degree"]      = _norm_degree(_first(RX_DEGREE, " ".join([prog,com])))
        row["start_term"]  = _first(RX_TERM, com)
        row["start_year"]  = _first(RX_YEAR, " ".join([dat,com]))
        row["intl_american"]= _norm_intl(_first(RX_INTL, com))
        row["gpa"]         = _first(RX_GPA, com)
        row["gre_total"]   = _first(RX_GRE_T, com)
        row["gre_verbal"]  = _first(RX_GRE_V, com)
        row["gre_aw"]      = _first(RX_GRE_AW, com)

        for k,v in list(row.items()):
            if isinstance(v,str):
                v = v.strip()
                row[k] = v if v else None

        # keep only rows that carry some signal
        if row["university"] or row["program"] or row["status"]:
            out.append(row)
    return out

# ---------- CARD/DIV FALLBACK ----------

def _rows_from_cards(soup: BeautifulSoup, page_url: str) -> List[Dict[str, Optional[str]]]:
    blocks = (
        soup.select("div.tw-flex.tw-items-center, div.tw-inline-flex.tw-items-center") or
        soup.select(".result-row, .c-result, .result, article, .search-result, .post, tr.result") or
        soup.select('div[class*="result"], section[class*="result"]') or []
    )
    rows=[]
    for b in blocks:
        row = _blank(page_url)
        # try common sub-elements (these names may not exist in Tailwind version)
        uni_el = b.select_one(".university, .institution, .c-institution, .inst, .td-institution")
        prog_el= b.select_one(".program, .c-program, .td-program")
        comm_el= b.select_one(".comments, .c-comments, .td-comments")
        date_el= b.select_one(".date, .c-date, time, .td-date")
        stat_el= b.select_one(".status, .c-decision, .decision, .td-decision")

        row["university"]= _txt(uni_el) or None
        row["program"]   = _txt(prog_el) or None
        row["comments"]  = _txt(comm_el) or None
        row["date_added"]= _txt(date_el) or _first(RX_DATE, _txt(b))
        row["status"]    = _norm_status(_txt(stat_el)) or _norm_status(_first(RX_STATUS, _txt(b)))

        blob=_txt(b)
        row["gpa"]        = _first(RX_GPA, blob)
        row["gre_total"]  = _first(RX_GRE_T, blob)
        row["gre_verbal"] = _first(RX_GRE_V, blob)
        row["gre_aw"]     = _first(RX_GRE_AW, blob)
        row["start_term"] = _first(RX_TERM, blob)
        row["start_year"] = _first(RX_YEAR, blob)
        row["intl_american"]= _norm_intl(_first(RX_INTL, blob))
        row["degree"]     = _norm_degree(_first(RX_DEGREE, blob) or row["program"])

        for k,v in list(row.items()):
            if isinstance(v,str):
                v=v.strip()
                row[k]=v if v else None

        if row["university"] or row["program"] or row["status"]:
            rows.append(row)
    return rows

# ---------- DRIVER ----------

def scrape_page(http: urllib3.PoolManager, url: str) -> List[Dict[str, Optional[str]]]:
    r = http.request("GET", url)
    if r.status != 200: return []
    soup = BeautifulSoup(r.data, "html.parser")

    table, idx = _find_results_table(soup)
    if table:
        return _rows_from_table(table, idx, url)
    # fallback
    return _rows_from_cards(soup, url)

def scrape_data(pages: int = 2, delay: float = 0.7, base_url: str = BASE) -> List[Dict[str, Optional[str]]]:
    http = make_http()
    out: List[Dict[str, Optional[str]]] = []
    for p in range(1, pages+1):
        url = base_url.format(page=p)
        out.extend(scrape_page(http, url))
        time.sleep(delay)
    return out

def save_data(rows: List[Dict[str, Optional[str]]], path: str = "applicant_data.json") -> None:
    for r in rows:
        for k in REQUIRED_KEYS:
            r.setdefault(k, None)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    data = scrape_data(pages=2, delay=0.7)
    save_data(data)
    print(f"wrote {len(data)} rows to applicant_data.json")