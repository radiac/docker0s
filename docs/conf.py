# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

import sphinx_radiac_theme  # noqa


# Make sure sphinx can find the source
sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../example/"))

from setup import find_version


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "docker0s"
copyright = "2022, Richard Terry"
author = "Richard Terry"
release = find_version("..", "docker0s", "__init__.py")

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_radiac_theme",
    "sphinx.ext.autodoc",
    "sphinx_gitref",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_radiac_theme"
html_static_path = ["_static"]

html_theme_options = {
    "analytics_id": "G-NH3KEN9NBN",
    "logo_only": False,
    "display_version": True,
    # Toc options
    "collapse_navigation": True,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
    # radiac.net theme
    "radiac_project_slug": "docker0s",
    "radiac_project_name": "docker0s",
    "radiac_subsite_links": [
        # ("https://radiac.net/projects/django-fastview/demo/", "Demo"),
    ],
}
