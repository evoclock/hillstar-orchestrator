"""Sphinx configuration for Hillstar Orchestrator documentation."""

import os
import sys

# -- Path setup ---------------------------------------------------------------
# Point Sphinx at the package root so autodoc can import all modules.
sys.path.insert(0, os.path.abspath("../.."))

# -- Project information ------------------------------------------------------
project = "Hillstar Orchestrator"
copyright = "2026, Julen Gamboa"
author = "Julen Gamboa"
release = "1.0.0"
version = "1.0.0"

# -- General configuration ----------------------------------------------------
extensions = [
	"sphinx.ext.autodoc",
	"sphinx.ext.napoleon",
	"sphinx.ext.intersphinx",
	"sphinx.ext.viewcode",
	"sphinx.ext.autosummary",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "_templates", "__pycache__"]

# Source file suffix
source_suffix = ".rst"
master_doc = "index"

# -- Napoleon settings (Google-style docstrings) ------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# -- Autodoc settings ---------------------------------------------------------
autodoc_default_options = {
	"members": True,
	"undoc-members": False,
	"show-inheritance": True,
	"member-order": "bysource",
}
autodoc_typehints = "description"
autodoc_class_signature = "separated"

# -- Autosummary settings -----------------------------------------------------
autosummary_generate = True

# -- Intersphinx (cross-project links) ----------------------------------------
intersphinx_mapping = {
	"python": ("https://docs.python.org/3", None),
	"requests": ("https://requests.readthedocs.io/en/latest/", None),
}

# -- HTML output --------------------------------------------------------------
html_theme = "furo"
html_title = "Hillstar Orchestrator"
html_static_path = ["_static"]
html_logo = "_static/Hillstar_icon_small.png"
html_favicon = "_static/Hillstar_icon_small.png"

html_theme_options = {
	"sidebar_hide_name": False,
	"navigation_with_keys": True,
}

# -- Options for autodoc mock imports -----------------------------------------
# Mock imports that may not be available in the build environment
autodoc_mock_imports = [
	"anthropic",
	"openai",
	"mistralai",
	"google.generativeai",
	"keyring",
	"tqdm",
]

# Suppress specific warnings for known docstring issues
suppress_warnings = [
	"ref.python",  # Ambiguous cross-references (e.g., ConfigurationError)
	"docutils",    # RST formatting in docstrings (markdown/RST collision)
]
