# MANIFEST

Map of the `eudoxys/{{{PACKAGE}}}` repository. Every tracked file is covered by
one row or glob below; check with `python .github/check_manifest.py`.
Update this file in the same PR that adds, moves, or deletes a file.

## Start here

1. `CLAUDE.md` — conventions and working rules
2. `DESIGN.md` — agreed design, decisions, planned modules
3. `{{{PACKAGE}}}/__init__.py` — package docs and public API
4. `{{{PACKAGE}}}/<core>.py` — the core model

## Task index

- Add a data source/class: copy `{{{PACKAGE}}}/<similar>.py`; export in `{{{PACKAGE}}}/__init__.py`; test in `{{{PACKAGE}}}/_test/test_<name>.py`; add rows here
- Change an output column: module docstring example, `{{{PACKAGE}}}/__init__.py` Data section, `README.md`, `DESIGN.md` columns table
- Add a CLI option: `{{{PACKAGE}}}/cli.py`, `{{{PACKAGE}}}/__init__.py` Syntax section
- Regenerate curated data: script named in the data table below; update that folder's `README.md`
- Release: `pyproject.toml` version; see the eudoxys-package skill checklist

## Package

| Path | Purpose | Notes |
|---|---|---|
| `{{{PACKAGE}}}/__init__.py` | package docs, re-exports | pdoc landing page |
| `{{{PACKAGE}}}/cli.py` | CLI `main()` | entry point `{{{PACKAGE}}}`; tested by `_test/test_cli.py` |

Add a row for each new module, naming the test that covers it.

## Tests and validation

| Path | Purpose | Notes |
|---|---|---|
| `{{{PACKAGE}}}/_test/README.md` | how to run tests | |
| `{{{PACKAGE}}}/_test/conftest.py` | cache location from env | |
| `{{{PACKAGE}}}/_test/test_*.py` | tests | fast unless marked `network` |
| `{{{PACKAGE}}}/_validate/README.md` | validation question, inputs, procedure, results | slow; run by hand |

## Data

None yet. When the package checks in data, add a table here with each file or
glob, whether it is curated or generated (and by which script), and its size.

## Repository

| Path | Purpose | Notes |
|---|---|---|
| `README.md` | user overview | |
| `CLAUDE.md` | assistant guidance | |
| `DESIGN.md` | package design | |
| `MANIFEST.md` | this file | |
| `CONTRIBUTING.md` | contributor guide | approved-issue rule |
| `TODO.md` | roadmap | |
| `pyproject.toml` | packaging | version here |
| `requirements.txt` | dependencies | |
| `Makefile` | `make docs` | |
| `LICENSE` | MIT | |
| `COPYRIGHT.md` | copyright notice | |
| `.gitignore` | | |
| `.gitattributes` | | |
| `{{{PACKAGE}}}/.gitignore` | generated-output ignores | |
| `.github/workflows/*.yaml` | CI: tests, docs, approved-issue check | |
| `.github/check_manifest.py` | checks this file | |

## Don't read

`docs/` (generated), `.venv/`, caches, `**/__marimo__/` session files, data files over ~1 MB.
