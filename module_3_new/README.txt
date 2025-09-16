Name / JHED
Mohammad Raza — mraza6

Module Info
EN.605.256 — Module 3: Databases & Querying

⸻

What this is
	•	PostgreSQL database with applicants table loaded from Module 2’s cleaned CSV + LLM JSONL.
	•	Query layer (query_data.py) with Q1–Q8 from assignment (Fall 2025 focus) + two additional questions.
	•	Flask page shows query results with two buttons: Pull Data (scrape/clean/load) and Update Analysis (refresh answers).
	•	Limitations write-up (limitations.pdf) on self-submitted data.

⸻

Approach
	1.	Load: load_data.py ingests Module 2 CSV/LLM output into Postgres (psycopg3).
	2.	Queries: SQL in query_data.py answers all required questions.
	3.	Web: Flask page displays results and supports Pull Data / Update Analysis.
	4.	Reused Module 2 llm_hosting/ inside Module 3 for standardization.

⸻

Requirements
	•	Python 3.10+
	•	PostgreSQL (local)
	•	psycopg[binary], flask

⸻

How to run it
	1.	Start PostgreSQL and ensure gradcafe DB exists.
	2.	Load data:
	python module_3_new/load_data.py --csv module_2_new/data/gradcafe_cleaned.csv \
  --llm-jsonl module_2_new/data/llm_extended.jsonl \
  --dsn postgresql://localhost/gradcafe --truncate
  3. Run queries:
  python module_3_new/query_data.py
  
  	4.	Launch Flask page (shows results + buttons).

⸻

Deliverables
	•	load_data.py — loader
	•	query_data.py — queries Q1–Q10
	•	llm_hosting/ — copied from Module 2
	•	limitations.pdf — two paragraphs
	•	README.md (this file)
	•	requirements.txt — psycopg[binary], flask
	•	Screenshots: console output + running webpage