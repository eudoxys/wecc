Testing
-------

From the repository root:

	python3 -m venv .venv
	. .venv/bin/activate
	python3 -m pip install --upgrade pip
	pip install -e . pytest
	pytest

Credentials needed (where they go, how to get them), what the first run
downloads, and roughly how long it takes.

Environment variables:

  - `{{{PACKAGE_UPPER}}}_CACHEDIR`: cache folder (default: the `cache` package default)
  - `{{{PACKAGE_UPPER}}}_TEST_BUILD=1`: build missing slow-test inputs instead of skipping

test_cli.py
-----------

Fast, self-contained checks that the package imports, reports a version, and
that the CLI handles `--help`, `--version`, and an unknown command. No network;
runs in under a second:

	pytest {{{PACKAGE}}}/_test/test_cli.py

Add a section like this one for each new `test_<name>.py`: what it checks, on
which case, whether it is fast/synthetic or networked, and how to run it alone.
