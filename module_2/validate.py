"""
Module 2 — validator
Checks applicant_data.json (raw) and llm_extend_applicant_data.json (cleaned).
Looks for:
- Row count (expect >= 30,000 for final run, but okay if smaller now).
- Missing required keys.
- Any lingering HTML fragments in text fields.
"""

import json, os

REQUIRED = {
  "program","university","comments","date_added","entry_url","status",
  "accept_date","reject_date","start_term","start_year","intl_american",
  "gre_total","gre_verbal","gre_aw","degree","gpa"
}

def check(path: str):
    if not os.path.exists(path):
        print(f"[!] {path} not found")
        return
    with open(path,"r",encoding="utf-8") as f:
        data = json.load(f)
    print(f"[{path}] rows:", len(data))
    # check required keys on first 1000 rows
    missing = set()
    for r in data[:1000]:
        missing |= (REQUIRED - set(r))
    if missing:
        print("Missing keys in sample:", sorted(missing))
    # scan for HTML-like fragments
    htmly = 0
    for r in data[:2000]:
        for k in ("program","university","comments"):
            v = r.get(k)
            if isinstance(v,str) and "<" in v and ">" in v:
                htmly += 1
                break
    print("Potential HTML fragments (first 2000 rows):", htmly)

if __name__=="__main__":
    check("applicant_data.json")
    check("llm_extend_applicant_data.json")