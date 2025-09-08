JHU Modern Software Concepts — Module 2: Web Scraping
Author: Mohammad Raza

What this is
	•	Scraper + cleaner + validator pipeline (GradCafe “computer science” query).
	•	Outputs raw JSON (applicant_data.json) and cleaned JSON (llm_extend_applicant_data.json).
	•	robots.txt checked — scraping allowed except /cgi-bin/ and /index-ad-test.php (screenshot.jpg).
	•	LLM hosting app included (llm_hosting/app.py), tested with sample_data.json.

What you need
	•	Python 3.10+
	•	urllib3, beautifulsoup4 (install from requirements.txt)
	•	certifi (macOS only, fixes SSL issue with urllib3)
	•	Virtual environment recommended

How to run it
	1.	cd module_2
	2.	python3 -m venv .venv
	3.	source .venv/bin/activate   (Windows: ..venv\Scripts\Activate.ps1)
	4.	pip install -r requirements.txt
	•	macOS only: pip install certifi
	5.	python scrape.py –pages 5 –delay 0.9
	6.	python clean.py
	7.	python validate.py

Where it runs
	•	Local only — runs from CLI, saves JSON files to module_2/.

Status
	•	Rows merged: 11,566 (applicant_data.json).
	•	Pipeline works end-to-end: scrape → clean → validate.
	•	Validator: 0 HTML fragments flagged in both raw and cleaned JSON.
	•	Query “computer science” appears exhausted. Scraper supports resume or broader queries.

Resume / More rows
	•	Resume from next page range:
python scrape.py --start 2000 --pages 5000 --delay 0.9
	•	Or broaden query (edit BASE in scrape.py):
BASE = "https://www.thegradcafe.com/survey/index.php?q=computer&page={page}"
Example:
python scrape.py --start 1 --pages 2000 --delay 0.9

Deliverables
	•	scrape.py → scraper with resume + dedup
	•	clean.py → data cleaner
	•	validate.py → checks row count, keys, HTML fragments
	•	applicant_data.json → raw scraped (11,566 rows)
	•	llm_extend_applicant_data.json → cleaned output
	•	requirements.txt → pinned dependencies
	•	README.txt → run instructions + notes (this file)
	•	screenshot.jpg → robots.txt proof

Challenges & Learnings
	•	Initial SSL verification failed on macOS → fixed with certifi.
	•	“computer science” query has fewer results than expected; broadened query instructions added.
	•	Learned how to stream JSONL + merge safely for resume.
	•	Full end-to-end run validated with ~11.5k rows.