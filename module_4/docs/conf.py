# -- Project information -----------------------------------------------------
project = "GradCafe Analysis"
author = "Mohammad Raza"
version = "1.0"
release = "1.0"

# -- General configuration ---------------------------------------------------
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Make the app package importable for autodoc (paths relative to module_4/docs/)
import os, sys
sys.path.insert(0, os.path.abspath(".."))                # module_4/
sys.path.insert(0, os.path.abspath("../src"))            # module_4/src

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]