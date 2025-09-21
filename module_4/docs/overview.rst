Overview & Setup
================
This is the Module 4 (Testing & Documentation) deliverable.

Local setup::

  python -m venv .venv
  source .venv/bin/activate
  python -m pip install -r module_4/requirements.txt
  pytest | tee module_4/coverage_summary.txt

Environment::

  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres