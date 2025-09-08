Checked robots.txt: https://www.thegradcafe.com/robots.txt  
As of 9/7/25: general scraping allowed. /cgi-bin/ and /index-ad-test.php are disallowed.  
Screenshot saved as screenshot.jpg.

LLM note: llm_hosting/app.py is included as required. Tested with sample_data.json.  
Depending on environment, llm_hosting/app.py may output an empty cleaned file.  
Main scraper/cleaner pipeline is tested separately and validated.  

Note: Installed certifi on macOS to resolve SSL/TLS verification with urllib3.  
This is just an environment fix, not a scraping dependency.  

==================================================
Module 2 – Submission Status
==================================================
- Rows merged: 11,566 (applicant_data.json)  
- Pipeline works end-to-end: scrape → clean → validate  
- Validator: 0 HTML fragments flagged in both raw and cleaned samples  
- Query “computer science” appears exhausted. Scraper supports resume or broader query.  

==================================================
How to Run
==================================================
cd module_2
# (optional) create venv
# python -m venv .venv && source .venv/bin/activate

pip install -r requirements.txt
# on macOS also run: pip install certifi

# Scrape (small demo)
python scrape.py --pages 5 --delay 0.9

# Clean
python clean.py

# Validate
python validate.py

==================================================
Resume / More Rows
==================================================
# Resume from next page range
python scrape.py --start 2001 --pages 2000 --delay 0.9

# Or broaden query (edit BASE in scrape.py):
# BASE = "https://www.thegradcafe.com/survey/index.php?q=computer&page={page}"
# Example:
python scrape.py --start 1 --pages 2000 --delay 0.9