# MANIFEST

Map of the `eudoxys/wecc` repository. Every tracked file is covered by
one row or glob below; check with `python .github/check_manifest.py`.
Update this file in the same PR that adds, moves, or deletes a file.

## Start here

1. `CLAUDE.md` — conventions and working rules
2. `DESIGN.md` — agreed design, decisions, planned modules
3. `wecc/__init__.py` — package docs and public API
4. `wecc/<core>.py` — the core model

## Task index

- Add a data source/class: copy `wecc/<similar>.py`; export in `wecc/__init__.py`; test in `wecc/_test/test_<name>.py`; add rows here
- Change an output column: module docstring example, `wecc/__init__.py` Data section, `README.md`, `DESIGN.md` columns table
- Add or refresh weather data: `wecc weather STATE YEAR [--refresh]` (`wecc/weather.py`)
- Add or refresh county load data: `wecc loads STATE YEAR [--refresh]` (`wecc/loads.py`); estimate harmonics in `wecc/clusters.csv`, `wecc/clusters_harmonics.csv`
- Add a CLI option: `wecc/cli.py`, `wecc/__init__.py` Syntax section
- Regenerate curated data: script named in the data table below; update that folder's `README.md`
- Release: `pyproject.toml` version; see the eudoxys-package skill checklist

## Package

| Path | Purpose | Notes |
|---|---|---|
| `wecc/__init__.py` | package docs, re-exports | pdoc landing page |
| `wecc/cli.py` | CLI `main()` | entry point `wecc`; tested by `_test/test_cli.py`, `_test/test_weather.py`, `_test/test_loads.py` |
| `wecc/weather.py` | add/refresh county weather files (`wecc weather STATE YEAR`) | tested by `_test/test_weather.py`; needs NSRDB credentials to download |
| `wecc/loads.py` | add/refresh county load files (`wecc loads STATE YEAR`) via the `loads` package | tested by `_test/test_loads.py`; needs NSRDB credentials to build; reads `clusters.csv`, `clusters_harmonics.csv` |
| `wecc/clusters_harmonics.csv` | TSGAM `[yearly,weekly,daily]` harmonics of each cluster medoid | curated; MAPE rows of `loads/_explore/explore_estimator_clusters.csv` (eudoxys/loads `4d31711`) |

Add a row for each new module, naming the test that covers it.

## Tests and validation

| Path | Purpose | Notes |
|---|---|---|
| `wecc/_test/README.md` | how to run tests | |
| `wecc/_test/conftest.py` | cache location from env | |
| `wecc/_test/test_*.py` | tests | fast unless marked `network` |
| `wecc/_validate/README.md` | validation question, inputs, procedure, results | slow; run by hand |

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
| `wecc/.gitignore` | generated-output ignores | |
| `.github/workflows/*.yaml` | CI: tests, docs, approved-issue check | |
| `.github/check_manifest.py` | checks this file | |

## Don't read

`docs/` (generated), `.venv/`, caches, `**/__marimo__/` session files, data files over ~1 MB.
