Architecture
============
- Flask app factory ``create_app``.
- Routes: ``/``, ``/analysis``, ``/pull``, ``/update``, ``/status``, ``/download.csv``.
- Dependency Injection: ``SCRAPER``/``LOADER``/``QUERY``/``REFRESH`` via ``app.config`` so tests use **fake/mocked** data (no real services).
- Template context: ``title``, ``busy``, ``msg``, ``summary``, ``blocks`` (including ``blocks.chart``).