# CLAUDE.md

Guidance for Claude when working in the `eudoxys/{{{PACKAGE}}}` repository.
General Eudoxys package conventions are in the `eudoxys-package` skill; this
file records only what is specific to this package.

## What this is

One paragraph: purpose, Python version, maturity, main inputs/outputs.

- Docs site: https://www.eudoxys.com/{{{PACKAGE}}} (pdoc from docstrings)
- Maintainer: David P. Chassin
- CLI entry point: `{{{PACKAGE}}}` -> `{{{PACKAGE}}}.cli:main`

## Where things are

- `MANIFEST.md`: map of every file, a task index, and what not to read.
  Read it first instead of listing folders.
- `DESIGN.md`: agreed design, numbered decisions, and planned modules. Follow
  its decisions; ask before departing from one.

Sibling Eudoxys dependencies and what each provides.

## Core conventions

Patterns every module follows (base classes, caching, argument names,
column/field naming, units and sign conventions, index/time conventions,
how missing data is handled).

## Style

House style details that differ from defaults.

## Build, test, docs

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install --upgrade pip && pip install -e . pytest
pytest
make docs
```

What is slow, what needs network or credentials, what CI runs.

## Known rough edges (don't "fix" silently; mention or ask)

- ...

## Working rules

- What must not be committed; which checked-in data is curated.
- What to update when a public API changes (docstring example, README,
  `DESIGN.md`).
- Update `MANIFEST.md` when adding, moving, or deleting files.
- The conventional small test case; avoid full rebuilds unprompted.
