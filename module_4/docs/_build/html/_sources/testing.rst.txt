Testing
=======
- pytest + pytest-cov with a 100% coverage gate on ``module_4.src.analysis_app``.
- Organization: name-based files, directory scoping (``module_4/tests``), and markers (web, buttons, analysis, db, integration).
- Use **fake/mocked** scraper/loader/query and a two-decimal percentage check per assignment.

Run tests::

  pytest | tee module_4/coverage_summary.txt