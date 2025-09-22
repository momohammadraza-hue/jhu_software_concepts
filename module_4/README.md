Mohammad Raza — mraza6

Module Info
EN.605.256 — Module 4: Testing, CI, and Documentation

What this is
- Carried forward the GradCafe analysis app from Module 3.
- Added comprehensive testing (pytest + coverage 100%).
- Integrated continuous integration (CI) via GitHub Actions.
- Created Sphinx documentation (API docs, architecture, testing, overview).
- Deliverables include proof of CI success and docs build screenshots.

Approach
1. Tests:
   - Unit tests for Flask routes, buttons, analysis page formatting.
   - Integration tests for end-to-end pull → update → render pipeline.
   - Parameterized and assertion-based examples included.
   - Coverage enforced at 100%.

2. Continuous Integration (CI):
   - Configured `.github/workflows/tests.yml` to run pytest on each push.
   - Coverage summary written to `module_4/coverage_summary.txt`.
   - CI success screenshots committed under `module_4/`.

3. Documentation (Sphinx):
   - `sphinx-quickstart` project under `module_4/docs`.
   - Configured `conf.py` for autodoc, napoleon, and Read the Docs theme.
   - Pages: Overview, API, Architecture, Testing.
   - Build proof included (`sphinx_success.png`).

Requirements
- Python 3.12+
- psycopg3, Flask, pytest, coverage, sphinx, sphinx-rtd-theme
- Virtual environment recommended (requirements.txt provided)

How to run it
1. Set up venv + deps:
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r module_4/requirements.txt

2. Run tests (local check):
   pytest | tee module_4/coverage_summary.txt

3. Run Flask app (manual):
   export DATABASE_URL=postgresql://localhost/postgres
   python -m module_4.src.analysis_app
   Open http://127.0.0.1:5000 in your browser.

4. Build docs (Sphinx):
   make -C module_4/docs html
   open module_4/docs/_build/html/index.html

Status
- All tests green with 100% coverage.
- CI workflow green on GitHub Actions.
- Sphinx docs build clean.
- Deliverables + screenshots included under `module_4/`.

Deliverables
- src/analysis_app.py — Flask app with dashboard routes
- tests/ — pytest suite (unit + integration)
- coverage_summary.txt — test coverage proof
- .github/workflows/tests.yml — CI workflow config
- docs/ — Sphinx documentation project
- actions_success.png — CI success proof
- sphinx_success.png — docs build proof
- README.md — this file

Repo Link
- Public GitHub Repository: https://github.com/momohammadraza-hue/jhu_software_concepts

Challenges & Learnings
- Learned pytest fixtures, monkeypatch, and parameterized tests.
- Debugged CI errors (module import paths, case sensitivity).
- Configured GitHub Actions with environment variables.
- Hands-on with Sphinx autodoc + Napoleon for docstring parsing.
- Gained experience integrating tests + CI + docs into a single repo workflow.

Grader Notes
- Tests cover all Flask routes and analysis logic.
- Coverage locked at 100% (per rubric).
- CI pipeline verified with screenshot.
- Sphinx docs include required sections and build proof.
- Code + docs kept lightweight and PEP8-compliant.