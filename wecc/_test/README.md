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

  - `WECC_CACHEDIR`: cache folder (default: the `cache` package default)
  - `WECC_TEST_BUILD=1`: build missing slow-test inputs instead of skipping

test_cli.py
-----------

Fast, self-contained checks that the package imports, reports a version, and
that the CLI handles `--help`, `--version`, and an unknown command. No network;
runs in under a second:

	pytest wecc/_test/test_cli.py

test_weather.py
-----------

Fast, self-contained checks of `wecc.weather` and `wecc weather`: state and
year validation, adding, skipping and refreshing files, atomic writes, failed
downloads leaving files intact, and missing credentials. NSRDB downloads are
replaced by synthetic data and files go to a temporary folder, so no network
or credentials are needed; runs in about 10 seconds:

	pytest wecc/_test/test_weather.py

test_loads.py
-------------

Fast, self-contained checks of `wecc.loads` and `wecc loads`: state and year
validation, medoid harmonics, which files each county and year requires,
adding, skipping and refreshing files, non-WECC counties, invalid builds
leaving files intact, finding files in the `loads` cache, and missing
credentials. Builds by the `loads` package are replaced by synthetic data and
files go to a temporary folder, so no network or credentials are needed; runs
in about 30 seconds:

	pytest wecc/_test/test_loads.py

Add a section like this one for each new `test_<name>.py`: what it checks, on
which case, whether it is fast/synthetic or networked, and how to run it alone.
