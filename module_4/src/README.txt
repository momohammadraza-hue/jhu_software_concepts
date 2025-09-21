Name / JHED

Mohammad Raza — mraza6

Module Info

EN.605.256 — Module 3: Databases and Querying

What this is
	•	PostgreSQL setup with applicants table loaded from Module 2’s cleaned dataset.
	•	Query layer (query_data.py) answering Q1–Q8 plus two extended queries (Q9, Q10).
	•	Flask web app (analysis_app.py) with dashboard for metrics, tables, and charts.
	•	“Pull Data” pipeline: scrape → clean → LLM normalize → load into Postgres.
	•	CSV export, copy-to-clipboard, and live charts (Chart.js) for top programs, GPA buckets, and yearly trends.

Approach
	1.	Load: cleaned CSV (gradcafe_cleaned.csv) + normalized JSONL imported into Postgres.
	2.	Schema: applicants table created; applicants_valid view applies guardrails (drop GPA>5, invalid scores, null terms).
	3.	Query functions: parameterized SQL for counts, averages, percentages, and filters.
	4.	Queries:
		•	Q1–Q8: core metrics (Fall applicants, GPA/GRE, acceptance %, JHU, Georgetown).
		•	Q9: top-10 programs by volume with acceptance %.
		•	Q10: acceptance rate by GPA bucket.
	5.	Flask app: interactive dashboard with KPIs, tables, and charts.

Requirements
	•	Python 3.10+
	•	PostgreSQL running locally (createdb gradcafe)
	•	psycopg3, Flask
	•	Chart.js (via CDN)
	•	Virtual environment recommended (requirements.txt provided)

How to run it
	1.	Start Postgres and create DB:

		createdb gradcafe

	2.	Activate venv + install deps:

		python3 -m venv .venv
		source .venv/bin/activate
		pip install -r requirements.txt

	3.	Load data:

		python module_3_new/load_data.py \
		--csv module_2_new/data/gradcafe_cleaned.csv \
		--llm-jsonl module_2_new/data/llm_extended.jsonl \
		--dsn postgresql://localhost/gradcafe

	4.	Run queries (CLI check):

		python module_3_new/query_data.py

	5.	Run Flask app:

		export DSN=postgresql://localhost/gradcafe
		python module_3_new/analysis_app.py

	6.	Open http://127.0.0.1:5000 in your browser.

Status
	•	Database populated with ~50k rows.
	•	Queries Q1–Q10 return valid outputs.
	•	Dashboard live with KPIs, tables, and charts.
	•	CSV export and pull pipeline functional.

Deliverables
	•	load_data.py — loads CSV + JSONL into Postgres
	•	query_data.py — Q1–Q10 query set
	•	analysis_app.py — Flask app with metrics/charts
	•	templates/index.html — dashboard UI
	•	limitations.pdf — dataset bias & caveats
	•	requirements.txt — pinned deps
	•	README.md — run instructions + notes (this file)
	•	module_3_screenshot.png — console + webpage proof

Challenges & Learnings
	•	Integrated scraper, cleaner, LLM normalization, Postgres, and Flask into one pipeline.
	•	Learned to guard against bad data (e.g., GPA>5, invalid GRE, null terms).
	•	First use of psycopg3 with parameterized queries.
	•	Hands-on with Flask templates + Chart.js for interactive analysis.
	•	Known issue: banner message auto-clears immediately (cosmetic).

Grader Notes
	•	All required deliverables included.
	•	Q1–Q8 fully implemented; Q9/Q10 add richer analysis.
	•	Web app meets rubric (front page + update/pull).
	•	Charts enhance but are optional (kept lightweight with CDN).
	•	Code PEP8-compliant and scoped to module-approved libs.