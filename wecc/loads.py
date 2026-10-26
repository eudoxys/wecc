"""WECC county load data maintenance

Adds or refreshes the checked-in county load files in `wecc/loads/` for one
WECC state and year, using the Eudoxys `loads` package
(https://www.eudoxys.com/loads) to build them.

Syntax
------

    wecc loads STATE YEAR [-r|--refresh] [-q|--quiet] [-d|--debug] [-w|--warning]

Arguments
---------

  - `STATE`: two-letter abbreviation of a WECC state (see `states()`)

  - `YEAR`: load year, from `FIRST_YEAR` through last year (the years for
    which `loads` can obtain the county's NSRDB weather)

  - `-r|--refresh`: rebuild and rewrite files that already exist (by default
    only missing files are added)

  - `-q|--quiet`: do not report progress per county

Description
-----------

Given a WECC state `ST` and a year `YYYY`, `update(ST,YYYY)` ensures that for
every county in that state the load files `loads` provides for that year
exist in

    wecc/loads/ST/COUNTY/

where `COUNTY` is the `fips` county name with spaces replaced by underscores.
A WECC state is any state with at least one county in the `fips` WECC region
(see `wecc.weather.states()`). The files are:

  1. **Reference data** (only when `YYYY` is `REFERENCE_YEAR`, i.e., 2018, the
     ResStock/ComStock year that `loads` is built on), for every county of the
     state:

     - `R.csv.gz`: residential load (`loads.residential.Residential`)

     - `C.csv.gz`: commercial load (`loads.commercial.Commercial`)

     - `T_elec_1h_training.csv.gz`: sector totals with 2018 weather
       (`loads.total.Total`)

     - `RSD.csv.gz`, ..., `CMW.csv.gz`: the raw ResStock and ComStock data of
       each building type found in the county (`loads.resstock.RESstock`,
       `loads.comstock.COMstock`); building types with no data in the county
       have no file.

     These are copies of the files `loads` writes in its cache, with the same
     names and contents as the files already checked in.

  2. **Load estimate** (any year), for every county with a cluster medoid in
     `clusters.csv` (the WECC counties):

     - `Estimate_YYYY.csv.gz`: hourly `elec_total_MW` predicted by
       `loads.estimator.Estimator` from the county's `YYYY` weather, using the
       TSGAM harmonics of the county's cluster medoid
       (`clusters_harmonics.csv`), exactly as `wecc_estimate.py` does for its
       2018-2022 estimate. The estimate is not calibrated to EIA energy (see
       `wecc_estimate.py` for that step).

Counties of the state that are outside WECC have no estimate, so for years
other than `REFERENCE_YEAR` they are reported as `skipped`.

Each file is expected to satisfy:

  1. **Shape.** The reference load files (`R`, `C`, `T_elec_1h_training`)
     and the estimate have one row per hour of their year, hour-beginning,
     indexed by a UTC timestamp (8760 rows, or 8784 in a leap year), and an
     `elec_total_MW` column with no missing values. The estimate has only
     that column (after the `timestamp` index).

  2. **Integrity.** A file is only replaced after the new data passes check 1
     (raw building type files must be non-empty CSV), and is written
     atomically, so an interrupted or failed run never leaves a partial file.
     Files are gzipped without a timestamp, so refreshing identical data
     leaves the file byte-for-byte unchanged.

A county whose build fails is reported and skipped; the remaining counties are
still processed. Files of that county written before the failure are kept.

Credentials
-----------

Building load data needs the county's NSRDB weather, which needs an NLR
(formerly NREL) developer key stored in `~/.nsrdb/credentials.json`. Run
`weather register` to obtain one. No credentials are needed when every
requested file already exists and `--refresh` is not given.

Examples
--------

Add the missing 2018 reference data and estimates for Nevada:

    wecc loads NV 2018

Add the 2023 estimates for Arizona (non-WECC counties are skipped):

    wecc loads AZ 2023

Rebuild all 2020 estimates for Oregon:

    wecc loads OR 2020 --refresh

From Python:

    from wecc.loads import update
    summary = update("NV",2018)

`summary` is a data frame indexed by county with the columns `status`
(`added`, `refreshed`, `unchanged`, `skipped`, or `failed`), `files` (the
number of files written), and `message`.

Caveats
-------

  - Builds go through the `loads` package, which keeps its own cached copy of
    each input and output in the `cache` package folder (`Cache.CACHEDIR`);
    `--refresh` also refreshes that cache for the files written here.

  - Building the reference data downloads ResStock, ComStock, Census, NLR and
    NSRDB data, and each estimate fits a TSGAM model, so a county takes
    minutes and a large state (TX) takes hours on an empty cache.

  - Only county files are maintained; the state files (`units.csv.gz`,
    `MWH_*`, `CF_*`, `T_*_1MS*`) and the package-wide files
    (`industry.csv.gz`, `agriculture.csv.gz`, `floorarea_*.csv.gz`) in
    `wecc/loads/` are not updated, nor are the existing multi-year
    `Estimate_2018-2022.csv.gz` files.

  - The files are not listed in `pyproject.toml` package-data, so they ship
    with a clone of the repository but not with a `pip install`.

  - Run this module as `python3 -m wecc.loads`, never as
    `python3 wecc/loads.py`, which would shadow the `loads` package.

References
----------

  - Eudoxys `loads`: https://www.eudoxys.com/loads

  - NREL ResStock and ComStock: https://resstock.nrel.gov/,
    https://comstock.nrel.gov/

  - NSRDB: https://nsrdb.nlr.gov/
"""

import os
import io
import sys
import glob
import gzip
import functools
import logging
import datetime as dt
import tempfile

import pandas as pd

from wecc import weather as _wecc_weather

_logger = logging.getLogger(__file__)

LOADSDIR = os.path.join(os.path.dirname(__file__),"loads")
"""Folder holding the checked-in county load files"""

CLUSTERS = os.path.join(os.path.dirname(__file__),"clusters.csv")
"""County cluster medoids (`county_st,medoid`), from `loads/clusters.csv`"""

HARMONICS = os.path.join(os.path.dirname(__file__),"clusters_harmonics.csv")
"""TSGAM harmonics of each cluster medoid (`medoid,yearly,weekly,daily`), the
MAPE rows of `loads/_explore/explore_estimator_clusters.csv`"""

FIRST_YEAR = 1998
"""First year of the NSRDB GOES aggregated v4 record (weather for estimates)"""

REFERENCE_YEAR = 2018
"""Year of the `loads` reference data (`loads.total.Total.TRAINING_YEAR`)"""

REFERENCE_FILES = ["R.csv.gz","C.csv.gz","T_elec_1h_training.csv.gz"]
"""Reference load files required for every county in `REFERENCE_YEAR`"""

ESTIMATE = "Estimate_{year}.csv.gz"
"""Name of the estimate file of a year"""

ENDUSE = "elec_total_MW"
"""Load column checked in every load file and kept in the estimate"""

STATUS = ["added","refreshed","unchanged","skipped","failed"]
"""Possible per-county outcomes reported by `update()`"""

def states() -> list[str]:
    """List the WECC states

    Returns
    -------

      - `list[str]`: sorted abbreviations of the states with at least one
        county in the `fips` WECC region
    """
    return _wecc_weather.states()

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
    return _wecc_weather.counties(state)

def harmonics(state:str,county:str) -> list[int]|None:
    """Get the TSGAM harmonics used to estimate a county's load

    Arguments
    ---------

      - `state`: state abbreviation

      - `county`: `fips` county name (spaces allowed)

    Returns
    -------

      - `list[int]|None`: `[yearly,weekly,daily]` harmonics of the county's
        cluster medoid, or `None` if the county has no medoid (it is not a
        WECC county)
    """
    return _harmonics(CLUSTERS,HARMONICS).get(f"{county} {state}")

@functools.cache
def _harmonics(clusters:str,best:str) -> dict[str,list[int]]:
    """@private Read the harmonics of every clustered county, by `"County ST"`"""
    clusters = pd.read_csv(clusters,index_col="county_st")
    best = pd.read_csv(best,index_col="medoid")
    return {county_st:[int(x) for x in best.loc[medoid,["yearly","weekly","daily"]]]
        for county_st,medoid in clusters.medoid.items()}

def pathname(state:str,county:str,name:str,folder:str|None=None) -> str:
    """Get the path of a county load file

    Arguments
    ---------

      - `state`: state abbreviation

      - `county`: `fips` county name (spaces allowed)

      - `name`: file name, e.g., `R.csv.gz` or `Estimate_2020.csv.gz`

      - `folder`: load data folder (default `LOADSDIR`)

    Returns
    -------

      - `str`: path name of the file `ST/COUNTY/name` in `folder`
    """
    return os.path.join(folder or LOADSDIR,state,county.replace(" ","_"),name)

def files(state:str,county:str,year:int) -> list[str]:
    """List the load files required for a county and year

    Arguments
    ---------

      - `state`: state abbreviation

      - `county`: `fips` county name (spaces allowed)

      - `year`: load year

    Returns
    -------

      - `list[str]`: `REFERENCE_FILES` if `year` is `REFERENCE_YEAR`, then
        the estimate file if the county has a cluster medoid; empty if
        `loads` provides nothing for the county in that year

    Raw building type files are not listed because they only exist for the
    building types found in the county.
    """
    result = list(REFERENCE_FILES) if year == REFERENCE_YEAR else []
    if harmonics(state,county) is not None:
        result.append(ESTIMATE.format(year=year))
    return result

def _check_year(year:int):
    """@private Raise `ValueError` if no load data can exist for `year`"""
    last = dt.date.today().year - 1
    if not isinstance(year,int) or not FIRST_YEAR <= year <= last:
        raise ValueError(f"{year=} is not available (valid years are {FIRST_YEAR} to {last})")

def _check_hours(data:pd.DataFrame,year:int,name:str):
    """@private Raise `ValueError` if a load frame does not satisfy the file contract"""
    if ENDUSE not in data.columns:
        raise ValueError(f"{name} has no {ENDUSE} column (columns are {list(data.columns)})")
    hours = pd.date_range(f"{year}-01-01",f"{year+1}-01-01",freq="1h",tz="UTC",inclusive="left")
    index = pd.DatetimeIndex(data.index)
    if index.tz is None or len(index) != len(hours) or not (index.tz_convert("UTC") == hours).all():
        raise ValueError(f"{name} expected {len(hours)} hourly UTC rows for {year}, got {len(index)}")
    if data[ENDUSE].isna().any():
        raise ValueError(f"{name} has missing {ENDUSE} values")

def _check_file(text:bytes,name:str,year:int):
    """@private Raise `ValueError` if a reference file's CSV text is not valid"""
    if name in REFERENCE_FILES:
        data = pd.read_csv(io.BytesIO(text),index_col=[0],parse_dates=[0])
        _check_hours(data,year,name)
    elif len(pd.read_csv(io.BytesIO(text),nrows=10)) == 0:
        raise ValueError(f"{name} has no data")

def _write(text:bytes,path:str):
    """@private Write CSV text to a file atomically, gzipped without a timestamp"""
    os.makedirs(os.path.dirname(path),exist_ok=True)
    fd,tmp = tempfile.mkstemp(dir=os.path.dirname(path),suffix=".tmp")
    try:
        with os.fdopen(fd,"wb") as raw, gzip.GzipFile(fileobj=raw,mode="wb",mtime=0,filename="") as fh:
            fh.write(text)
        os.replace(tmp,path)
    except BaseException:
        os.remove(tmp)
        raise

def _cachefile(state:str,county:str,name:str) -> str|None:
    """@private Find a county file in the `loads` cache (latest cache version)"""
    from cache import Cache # pylint: disable=import-outside-toplevel
    found = {}
    for path in glob.glob(os.path.join(glob.escape(Cache.CACHEDIR),"loads","*",state,county,name)):
        version = path[len(Cache.CACHEDIR):].split(os.sep)[2]
        if version.isdigit():
            found[int(version)] = path
    return found[max(found)] if found else None

def _reference(state:str,county:str,refresh:bool=False) -> dict[str,bytes]:
    """@private Build a county's reference data with `loads`

    Returns the CSV text of every reference and building type file found in
    the `loads` cache, by file name.
    """
    # pylint: disable=import-outside-toplevel
    from loads.resstock import RESstock
    from loads.comstock import COMstock
    from loads.residential import Residential
    from loads.commercial import Commercial
    from loads.total import Total

    # building the parts in order with refresh, because refresh is not
    # passed down by Residential, Commercial and Total
    for btype in RESstock.BUILDING_TYPES:
        RESstock(state,county,btype,refresh=refresh)
    for btype in COMstock.BUILDING_TYPES:
        COMstock(state,county,btype,refresh=refresh)
    Residential(state,county,refresh=refresh)
    Commercial(state,county,refresh=refresh)
    Total(state,county,refresh=refresh)

    result = {}
    names = REFERENCE_FILES + [f"{x}.csv.gz" for x in list(RESstock.BUILDING_TYPES)+list(COMstock.BUILDING_TYPES)]
    for name in names:
        path = _cachefile(state,county,name)
        if path is None:
            if name in REFERENCE_FILES:
                raise RuntimeError(f"loads did not produce {name}")
            _logger.debug(f"{state} {county} has no {name}")
            continue
        with gzip.open(path,"rb") as fh:
            result[name] = fh.read()
    return result

def _estimate(state:str,county:str,year:int,harmonic:list[int],refresh:bool=False) -> pd.DataFrame: # pylint: disable=unused-argument
    """@private Estimate a county's hourly load for a year with `loads`

    `refresh` is not used: the estimate is always recomputed, from the
    `loads` cache of its inputs.
    """
    # pylint: disable=import-outside-toplevel
    from loads.estimator import Estimator, EstimatorConfig

    config = EstimatorConfig(harmonics=harmonic,enduse=ENDUSE)
    data = Estimator(f"{county} {state}",[year],config=config)[[ENDUSE]]
    data.index = pd.DatetimeIndex(data.index).tz_convert("UTC")
    hours = pd.date_range(f"{year}-01-01",f"{year+1}-01-01",freq="1h",tz="UTC",inclusive="left",name="timestamp")
    # leading hours are undefined by exogenous lags (as in wecc_estimate.py)
    return data.reindex(hours).interpolate(limit_direction="both")

def _update_county( # pylint: disable=too-many-arguments,too-many-positional-arguments
        state:str,
        county:str,
        year:int,
        harmonic:list[int]|None,
        refresh:bool,
        folder:str|None,
        ) -> tuple[list[str],list[str]]:
    """@private Write a county's files, returning the names of the files added and refreshed"""
    added,refreshed = [],[]

    def save(name,text):
        path = pathname(state,county,name,folder)
        if os.path.exists(path):
            if not refresh:
                return
            refreshed.append(name)
        else:
            added.append(name)
        _write(text,path)

    if year == REFERENCE_YEAR:
        for name,text in _reference(state,county,refresh=refresh).items():
            _check_file(text,name,year)
            save(name,text)

    if harmonic is not None:
        name = ESTIMATE.format(year=year)
        if refresh or not os.path.exists(pathname(state,county,name,folder)):
            data = _estimate(state,county,year,harmonic,refresh=refresh)
            if list(data.columns) != [ENDUSE]:
                raise ValueError(f"{name} unexpected columns {list(data.columns)}")
            _check_hours(data,year,name)
            data.index.name = "timestamp"
            save(name,data.to_csv(index=True,header=True).encode())

    return added,refreshed

def update(
        state:str,
        year:int,
        refresh:bool=False,
        folder:str|None=None,
        ) -> pd.DataFrame:
    """Add or refresh the load files of every county in a WECC state

    Arguments
    ---------

      - `state`: WECC state abbreviation

      - `year`: load year

      - `refresh`: rebuild and rewrite files that already exist

      - `folder`: load data folder (default `LOADSDIR`)

    Returns
    -------

      - `pandas.DataFrame`: one row per county (index `county`) with columns
        `status` (one of `STATUS`), `files` (number of files written), and
        `message`

    Exceptions
    ----------

      - `ValueError`: `state` is not a WECC state or `year` is out of range

      - `RuntimeError`: builds are needed and NSRDB credentials are missing

    Per-county build failures do not raise; they are reported with status
    `failed`.
    """
    state = str(state).upper()
    names = counties(state)
    _check_year(year)

    required = {x:files(state,x,year) for x in names}
    todo = [x for x in names if required[x] and (refresh
        or not all(os.path.exists(pathname(state,x,y,folder)) for y in required[x]))]
    if todo:
        _wecc_weather._check_credentials() # pylint: disable=protected-access

    result = []
    for n,county in enumerate(names,1):
        if not required[county]:
            result.append([county,"skipped",0,f"no load data for {year} (not a WECC county)"])
            _logger.debug(f"{state} {county} {year} skipped")
            continue
        if county not in todo:
            result.append([county,"unchanged",0,"files exist"])
            _logger.debug(f"{state} {county} {year} files exist")
            continue
        try:
            added,refreshed = _update_county(state,county,year,harmonics(state,county),refresh,folder)
            status = "added" if added else "refreshed" if refreshed else "unchanged"
            result.append([county,status,len(added)+len(refreshed),None])
            _logger.info(f"[{n}/{len(names)}] {state} {county} {year} {status}")
        except Exception as err: # pylint: disable=broad-exception-caught
            result.append([county,"failed",0,str(err) or type(err).__name__])
            _logger.warning(f"[{n}/{len(names)}] {state} {county} {year} failed ({err})")

    return pd.DataFrame(result,columns=["county","status","files","message"]).set_index("county")

if __name__ == "__main__":

    # maintenance usage: python3 -m wecc.loads STATE YEAR [--refresh] [--debug]
    logging.basicConfig(level=logging.DEBUG if "--debug" in sys.argv else logging.INFO)
    _args = [x for x in sys.argv[1:] if not x.startswith("--")]
    print(update(_args[0],int(_args[1]),refresh="--refresh" in sys.argv).to_string())
