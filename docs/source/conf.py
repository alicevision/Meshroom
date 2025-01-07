# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
from pathlib import Path
import sys

os.environ['PROJECT_DIR'] = Path('../..').resolve().as_posix()

sys.path.append(os.path.abspath(os.getenv('PROJECT_DIR')))
sys.path.append(os.path.abspath('./_ext'))

project = 'Meshroom'
copyright = '2025, AliceVision Association'
author = 'AliceVision Association'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'fetch_md',
    'meshroom_doc',
    'sphinx.ext.graphviz',
    'sphinx.ext.inheritance_diagram'
]

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
