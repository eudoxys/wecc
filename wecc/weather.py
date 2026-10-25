"""WECC county weather data maintenance

Adds or refreshes the checked-in county weather files in `wecc/weather/` for
one WECC state and year, using the Eudoxys `weather` package
(https://www.eudoxys.com/weather) to obtain NSRDB actual weather.

Syntax
------

    wecc weather STATE YEAR [-r|--refresh] [-q|--quiet] [-d|--debug] [-w|--warning]

Arguments
---------

  - `STATE`: two-letter abbreviation of a WECC state (see `states()`)

  - `YEAR`: weather year, from `FIRST_YEAR` through last year; years NSRDB
    has not published yet fail per county

  - `-r|--refresh`: download and rewrite files that already exist (by default
    only missing files are added)

  - `-q|--quiet`: do not report progress per county

Description
-----------

Given a WECC state `ST` and a year `YYYY`, `update(ST,YYYY)` ensures that for
every county in that state the file

    wecc/weather/ST/COUNTY/W_YYYY.csv.gz

exists, where `COUNTY` is the `fips` county name with spaces replaced by
underscores. A WECC state is any state with at least one county in the `fips`
WECC region, and all of its counties are covered, including those outside
WECC (e.g., all 254 TX counties), as the checked-in data always has been.

Each file is expected to satisfy:

  1. **Columns.** `timestamp` (index), `temperature_degF`, `humidity_pc`,
     `global_Wpms`, `direct_Wpms`, `diffuse_Wpms`, as produced by
     `weather.Weather(state,county,year)`.

  2. **Shape.** One row per hour of the year, hour-beginning, in UTC
     (8760 rows, or 8784 in a leap year).

  3. **Integrity.** A file is only replaced after the new data passes checks 1
     and 2, and is written atomically, so an interrupted or failed run never
     leaves a partial file. Files are gzipped without a timestamp, so
     refreshing identical data leaves the file byte-for-byte unchanged.

A county whose download fails is reported and skipped; the remaining counties
are still processed.

Credentials
-----------

Downloading NSRDB data needs an NLR (formerly NREL) developer key stored in
`~/.nsrdb/credentials.json`. Run `weather register` to obtain one. No
credentials are needed when every requested file already exists and
`--refresh` is not given.

Examples
--------

Add any missing 2023 files for Nevada:

    wecc weather NV 2023

Re-download all 2022 files for Arizona:

    wecc weather AZ 2022 --refresh

From Python:

    from wecc.weather import update
    summary = update("NV",2023)

`summary` is a data frame indexed by county with the columns `status`
(`added`, `refreshed`, `unchanged`, or `failed`), `rows`, and `message`.

Caveats
-------

  - Downloads go through the `weather` package, which also keeps its own
    cached copy of each county-year in the `cache` package folder.

  - NSRDB downloads take several seconds per county and are rate limited by
    NLR; a large state (TX) takes a long time.

  - The files are not listed in `pyproject.toml` package-data, so they ship
    with a clone of the repository but not with a `pip install`.

  - Run this module as `python3 -m wecc.weather`, never as
    `python3 wecc/weather.py`, which would shadow the `weather` package.

References
----------

  - NSRDB: https://nsrdb.nlr.gov/

  - Eudoxys `weather`: https://www.eudoxys.com/weather
"""

import os
import sys
import gzip
import logging
import datetime as dt
import tempfile

import pandas as pd

from weather import weather as _weather # Eudoxys weather package, not this module
from fips.counties import Counties

_logger = logging.getLogger(__file__)

WEATHERDIR = os.path.join(os.path.dirname(__file__),"weather")
"""Folder holding the checked-in county weather files"""

FIRST_YEAR = 1998
"""First year of the NSRDB GOES aggregated v4 record"""

COLUMNS = ["temperature_degF","humidity_pc","global_Wpms","direct_Wpms","diffuse_Wpms"]
"""Columns of every weather file (after the `timestamp` index)"""

STATUS = ["added","refreshed","unchanged","failed"]
"""Possible per-county outcomes reported by `update()`"""

def states() -> list[str]:
    """List the WECC states

    Returns
    -------

      - `list[str]`: sorted abbreviations of the states with at least one
        county in the `fips` WECC region
    """
    data = Counties(use_index=["RO","ST","COUNTY"])
    return sorted(set(data.loc["WECC"].index.get_level_values("ST")))

def counties(state:str) -> list[str]:
    """List all counties of a WECC state

    Arguments
    ---------

      - `state`: state abbreviation

    Returns
    -------

      - `list[str]`: sorted `fips` county names (with spaces)

    Exceptions
    ----------

      - `ValueError`: `state` is not a WECC state
    """
    wecc = states()
    if state not in wecc:
        raise ValueError(f"{state=} is not a WECC state (valid states are {', '.join(wecc)})")
    names = Counties(use_index=["ST","COUNTY"]).loc[[state]].index.get_level_values("COUNTY")
    return sorted(names)

def pathname(state:str,county:str,year:int,folder:str|None=None) -> str:
    """Get the path of a county weather file

    Arguments
    ---------

      - `state`: state abbreviation

      - `county`: `fips` county name (spaces allowed)

      - `year`: weather year

      - `folder`: weather data folder (default `WEATHERDIR`)

    Returns
    -------

      - `str`: path name of the file `ST/COUNTY/W_YYYY.csv.gz` in `folder`
    """
    return os.path.join(folder or WEATHERDIR,state,county.replace(" ","_"),f"W_{year}.csv.gz")

def _check_year(year:int):
    """@private Raise `ValueError` if no year of data can exist for `year`"""
    last = dt.date.today().year - 1
    if not isinstance(year,int) or not FIRST_YEAR <= year <= last:
        raise ValueError(f"{year=} is not available (valid years are {FIRST_YEAR} to {last})")

def _check_credentials():
    """@private Raise `RuntimeError` if the NSRDB credentials file is missing

    The `weather` package opens a sign-up page in a browser and then fails
    obscurely when credentials are missing, so check before downloading.
    """
    path = _weather.CREDENTIALS.format(HOME=os.environ.get("HOME","~"))
    if not os.path.exists(path):
        raise RuntimeError(f"NSRDB credentials not found in {path} "
            "(run `weather register` to obtain an access token)")

def _check_data(data:pd.DataFrame,year:int):
    """@private Raise `ValueError` if the data does not satisfy the file contract"""
    if list(data.columns) != COLUMNS:
        raise ValueError(f"unexpected columns {list(data.columns)}")
    hours = pd.date_range(f"{year}-01-01",f"{year+1}-01-01",freq="1h",tz="UTC",inclusive="left")
    index = pd.DatetimeIndex(data.index)
    if index.tz is None or len(index) != len(hours) or not (index.tz_convert("UTC") == hours).all():
        raise ValueError(f"expected {len(hours)} hourly UTC rows for {year}, got {len(index)}")

def _write(data:pd.DataFrame,path:str):
    """@private Write a weather file atomically, gzipped without a timestamp"""
    os.makedirs(os.path.dirname(path),exist_ok=True)
    data = data.copy()
    data.index.name = "timestamp"
    fd,tmp = tempfile.mkstemp(dir=os.path.dirname(path),suffix=".tmp")
    try:
        with os.fdopen(fd,"wb") as raw, gzip.GzipFile(fileobj=raw,mode="wb",mtime=0,filename="") as fh:
            fh.write(data.to_csv(index=True,header=True).encode())
        os.replace(tmp,path)
    except BaseException:
        os.remove(tmp)
        raise

def update(
        state:str,
        year:int,
        refresh:bool=False,
        folder:str|None=None,
        ) -> pd.DataFrame:
    """Add or refresh the weather files of every county in a WECC state

    Arguments
    ---------

      - `state`: WECC state abbreviation

      - `year`: weather year

      - `refresh`: download and rewrite files that already exist

      - `folder`: weather data folder (default `WEATHERDIR`)

    Returns
    -------

      - `pandas.DataFrame`: one row per county (index `county`) with
        columns `status` (one of `STATUS`), `rows`, and `message`

    Exceptions
    ----------

      - `ValueError`: `state` is not a WECC state or `year` is out of range

      - `RuntimeError`: downloads are needed and NSRDB credentials are missing

    Per-county download failures do not raise; they are reported with status
    `failed`.
    """
    state = str(state).upper()
    names = counties(state)
    _check_year(year)

    todo = [x for x in names if refresh or not os.path.exists(pathname(state,x,year,folder))]
    if todo:
        _check_credentials()

    result = []
    for n,county in enumerate(names,1):
        path = pathname(state,county,year,folder)
        existed = os.path.exists(path)
        if county not in todo:
            result.append([county,"unchanged",None,"file exists"])
            _logger.debug(f"{path} exists")
            continue
        try:
            data = _weather.Weather(state,county,year,refresh=refresh)
            _check_data(data,year)
            _write(pd.DataFrame(data),path)
            status = "refreshed" if existed else "added"
            result.append([county,status,len(data),None])
            _logger.info(f"[{n}/{len(names)}] {state} {county} {year} {status}")
        except Exception as err: # pylint: disable=broad-exception-caught
            result.append([county,"failed",None,str(err) or type(err).__name__])
            _logger.warning(f"[{n}/{len(names)}] {state} {county} {year} failed ({err})")

    return pd.DataFrame(result,columns=["county","status","rows","message"]).set_index("county")

if __name__ == "__main__":

    # maintenance usage: python3 -m wecc.weather STATE YEAR [--refresh] [--debug]
    logging.basicConfig(level=logging.DEBUG if "--debug" in sys.argv else logging.INFO)
    _args = [x for x in sys.argv[1:] if not x.startswith("--")]
    print(update(_args[0],int(_args[1]),refresh="--refresh" in sys.argv).to_string())
