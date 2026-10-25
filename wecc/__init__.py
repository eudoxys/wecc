"""WECC data in support of other Eudoxys packages

Syntax
------

    wecc COMMAND [-h] [--version] [-d] [-w] [OPTIONS ...]
    wecc weather STATE YEAR [-r|--refresh] [-q|--quiet]
    wecc loads STATE YEAR [-r|--refresh] [-q|--quiet]

Positional arguments
--------------------

  - `COMMAND`: one of

    - `weather`: add (or with `--refresh`, re-download) the county weather
      files `wecc/weather/STATE/COUNTY/W_YEAR.csv.gz` for every county of a
      WECC state, from NSRDB via the Eudoxys `weather` package (see
      `wecc.weather`)

    - `loads`: add (or with `--refresh`, rebuild) the county load files in
      `wecc/loads/STATE/COUNTY/` for every county of a WECC state, using the
      Eudoxys `loads` package: the 2018 reference data when `YEAR` is 2018,
      and the hourly load estimate `Estimate_YEAR.csv.gz` of each WECC county
      (see `wecc.loads`)

Optional arguments
------------------

  - `-d|--debug`: enable debug logging and traceback on exceptions

  - `-h|--help`: show this help message and exit

  - `--version`: show the package version and exit

  - `-w|--warning`: enable warning messages from python

Description
-----------

What the package is for. Then, as a specification:

Given ..., `wecc.module.Class` returns ... that is expected to satisfy:

  1. **Shape.** ...

  2. **Invariants.** ...

  3. **Repeatability.** ...

What is not promised
--------------------

  - Known limits, untested regions, things not yet modeled.

Data
----

  - `field_units`: definition, units, sign convention.

```mermaid
flowchart LR
    source[(External data)] --> Class --> output[Result]
```

Citation
--------

To cite this dataset or package use the following:

  - Chassin, David P., "WECC data in support of other Eudoxys packages" (2026). URL:
    https://www.eudoxys.com/wecc.
"""

try:
    import importlib.metadata
    __version__ = importlib.metadata.version("wecc")
except Exception: # pylint: disable=broad-exception-caught
    __version__ = "dev"

# re-export the public API
# from wecc.module import Class
from wecc.cli import main
