# -- General configuration ---------------------------------------------------
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
autodoc_mock_imports = ["psycopg", "psycopg2", "psycopg2-binary"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Make the packages importable for autodoc
import os, sys
HERE = os.path.abspath(os.path.dirname(__file__))          # module_4/docs
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))     # repo root
MOD4 = os.path.join(ROOT, "module_4")                      # module_4/
SRC = os.path.join(MOD4, "src")                            # module_4/src

for p in (ROOT, MOD4, SRC):
    if p not in sys.path:
        sys.path.insert(0, p)

# -- HTML theme --------------------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]