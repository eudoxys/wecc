<!--
Template for a new Eudoxys package; delete this comment once filled in.
Follow the eudoxys-package skill (github.com/eudoxys/claude), section 13.

1. Replace these placeholders in every file:
     {{{PACKAGE}}}              package/repo/import name, e.g. loads
     {{{PACKAGE_UPPER}}}        the same in upper case, for env vars, e.g. LOADS
     {{{PACKAGE_DESCRIPTION}}}  one-line description
     {{{YEAR}}}                 year, for COPYRIGHT.md and the citation in __init__.py
   and rename the {{{PACKAGE}}}/ folder to the package name.
2. Fill in the prose placeholders in README.md, CLAUDE.md, DESIGN.md (or
   delete it if the design fits in the package docstring), and TODO.md.
3. Enable GitHub Pages (source: GitHub Actions).
4. Run `pytest`, `make docs`, and `python .github/check_manifest.py`.
-->

[![Validation](https://github.com/eudoxys/{{{PACKAGE}}}/actions/workflows/validate.yaml/badge.svg)](https://github.com/eudoxys/{{{PACKAGE}}}/actions/workflows/validate.yaml)
[![Documentation](https://github.com/eudoxys/{{{PACKAGE}}}/actions/workflows/deploy-pages.yaml/badge.svg)](https://github.com/eudoxys/{{{PACKAGE}}}/actions/workflows/deploy-pages.yaml)

{{{PACKAGE_DESCRIPTION}}}

One paragraph: what `{{{PACKAGE}}}` produces, from what inputs, and for whom.

# Documentation

See https://www.eudoxys.com/{{{PACKAGE}}}

# Installation

Install using Eudoxys Package Manager:

    pip install --upgrade git+https://github.com/eudoxys/epm
    epm install {{{PACKAGE}}}

Install using `pip`:

    pip install git+https://github.com/eudoxys/{{{PACKAGE}}}

# Maintenance

## Update docs

    make docs

## Run tests

    pip install -e . pytest
    pytest

Note any credentials or downloads the tests need and link to
[`{{{PACKAGE}}}/_test/README.md`]({{{PACKAGE}}}/_test/README.md).

## Cache build

(If the package caches data) how to rebuild, back up, and restore the cache,
and how long a full rebuild takes.

# Examples

## Command line

    {{{PACKAGE}}} print ...

## Python

    from {{{PACKAGE}}} import Class
    print(Class(...))

with its real output.
