<!--
Template for a new Eudoxys package; delete this comment once filled in.
Follow the eudoxys-package skill (github.com/eudoxys/claude), section 13.

1. (Done) Template placeholders replaced: package `wecc`, env prefix `WECC`,
   year 2026; folder renamed to `wecc/`.
2. Fill in the prose placeholders in README.md, CLAUDE.md, DESIGN.md (or
   delete it if the design fits in the package docstring), and TODO.md.
3. Enable GitHub Pages (source: GitHub Actions).
4. Run `pytest`, `make docs`, and `python .github/check_manifest.py`.
-->

[![Validation](https://github.com/eudoxys/wecc/actions/workflows/validate.yaml/badge.svg)](https://github.com/eudoxys/wecc/actions/workflows/validate.yaml)
[![Documentation](https://github.com/eudoxys/wecc/actions/workflows/deploy-pages.yaml/badge.svg)](https://github.com/eudoxys/wecc/actions/workflows/deploy-pages.yaml)

WECC data in support of other Eudoxys packages

One paragraph: what `wecc` produces, from what inputs, and for whom.

# Documentation

See https://www.eudoxys.com/wecc

# Installation

Install using Eudoxys Package Manager:

    pip install --upgrade git+https://github.com/eudoxys/epm
    epm install wecc

Install using `pip`:

    pip install git+https://github.com/eudoxys/wecc

# Maintenance

## Update docs

    make docs

## Run tests

    pip install -e . pytest
    pytest

Note any credentials or downloads the tests need and link to
[`wecc/_test/README.md`](wecc/_test/README.md).

## Cache build

(If the package caches data) how to rebuild, back up, and restore the cache,
and how long a full rebuild takes.

# Examples

## Command line

    wecc print ...

## Python

    from wecc import Class
    print(Class(...))

with its real output.
