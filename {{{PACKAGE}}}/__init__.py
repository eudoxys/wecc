"""{{{PACKAGE_DESCRIPTION}}}

Syntax
------

    {{{PACKAGE}}} COMMAND [-h] [--version] [-d] [-w] [OPTIONS ...]

Positional arguments
--------------------

  - `COMMAND`: what it does

Optional arguments
------------------

  - `-d|--debug`: enable debug logging and traceback on exceptions

  - `-h|--help`: show this help message and exit

  - `--version`: show the package version and exit

  - `-w|--warning`: enable warning messages from python

Description
-----------

What the package is for. Then, as a specification:

Given ..., `{{{PACKAGE}}}.module.Class` returns ... that is expected to satisfy:

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

  - Chassin, David P., "{{{PACKAGE_DESCRIPTION}}}" ({{{YEAR}}}). URL:
    https://www.eudoxys.com/{{{PACKAGE}}}.
"""

try:
    import importlib.metadata
    __version__ = importlib.metadata.version("{{{PACKAGE}}}")
except Exception: # pylint: disable=broad-exception-caught
    __version__ = "dev"

# re-export the public API
# from {{{PACKAGE}}}.module import Class
from {{{PACKAGE}}}.cli import main
