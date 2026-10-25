"""Fast tests of `wecc.weather` and `wecc weather`

NSRDB downloads are replaced by synthetic data, so these tests need no
network or credentials. Files are written to a temporary folder.
"""

import os
import gzip

import pandas as pd
import pytest

from wecc import weather
from wecc.cli import main

YEAR = 2020 # leap year: 8784 hours

def _synthetic(state,county,year,refresh=False): # pylint: disable=unused-argument
    """Stand-in for `weather.Weather` returning a valid hourly year"""
    index = pd.date_range(f"{year}-01-01",periods=8784 if year%4==0 else 8760,freq="1h",tz="UTC")
    return pd.DataFrame({x:1.0 for x in weather.COLUMNS},index=index)

@pytest.fixture(name="setup")
def fixture_setup(tmp_path,monkeypatch):
    """Redirect output to a temporary folder and stub out the download"""
    calls = []
    def fake(*args,**kwargs):
        calls.append(args)
        return _synthetic(*args,**kwargs)
    monkeypatch.setattr(weather,"WEATHERDIR",str(tmp_path))
    monkeypatch.setattr(weather._weather,"Weather",fake) # pylint: disable=protected-access
    monkeypatch.setattr(weather,"_check_credentials",lambda:None)
    return tmp_path,calls

def test_states():
    """WECC states include the western states and the partial ones"""
    assert {"AZ","CA","CO","ID","MT","NM","NV","OR","SD","TX","UT","WA","WY"} <= set(weather.states())
    assert "NY" not in weather.states()

def test_counties():
    """All counties of a WECC state are listed, not just its WECC counties"""
    assert len(weather.counties("NV")) == 17
    assert len(weather.counties("TX")) == 254

def test_pathname():
    """County folder names use underscores for spaces"""
    path = weather.pathname("CA","Los Angeles",2020,"/x")
    assert path == "/x/CA/Los_Angeles/W_2020.csv.gz"

@pytest.mark.parametrize("state,year",[("NY",YEAR),("XX",YEAR),("NV",1990),("NV",2999)])
def test_bad_arguments(state,year,setup):
    """Non-WECC states and impossible years are rejected before any download"""
    with pytest.raises(ValueError):
        weather.update(state,year)
    assert not setup[1]

def test_add_then_skip_then_refresh(setup):
    """Missing files are added, existing ones kept unless refreshed"""
    folder,calls = setup
    result = weather.update("NV",YEAR)
    assert (result.status=="added").all() and len(result) == 17
    path = weather.pathname("NV","White Pine",YEAR)
    data = pd.read_csv(path,index_col=["timestamp"],parse_dates=["timestamp"])
    assert list(data.columns) == weather.COLUMNS and len(data) == 8784
    with open(path,"rb") as fh:
        before = fh.read()

    calls.clear()
    result = weather.update("NV",YEAR)
    assert (result.status=="unchanged").all() and not calls

    result = weather.update("NV",YEAR,refresh=True)
    assert (result.status=="refreshed").all() and len(calls) == 17
    with open(path,"rb") as fh:
        assert fh.read() == before, "identical data must give identical bytes"
    assert not [x for x in os.listdir(os.path.dirname(path)) if x.endswith(".tmp")]
    assert str(folder) in path

def test_failure_keeps_file(setup,monkeypatch):
    """A failed or invalid download is reported and leaves existing files intact"""
    weather.update("NV",YEAR)
    path = weather.pathname("NV","Clark",YEAR)
    def bad(state,county,year,refresh=False):
        if county == "Clark":
            return _synthetic(state,county,year).iloc[:-1] # one hour short
        raise RuntimeError("download failed")
    monkeypatch.setattr(weather._weather,"Weather",bad) # pylint: disable=protected-access
    result = weather.update("NV",YEAR,refresh=True)
    assert (result.status=="failed").all()
    with gzip.open(path,"rt") as fh:
        assert len(fh.readlines()) == 8785

def test_missing_credentials(tmp_path,monkeypatch):
    """Downloads without credentials fail with a clear message"""
    monkeypatch.setattr(weather,"WEATHERDIR",str(tmp_path))
    monkeypatch.setenv("HOME",str(tmp_path))
    with pytest.raises(RuntimeError,match="weather register"):
        weather.update("NV",YEAR)

def test_cli(setup,capsys):
    """`wecc weather STATE YEAR` updates the state and summarizes"""
    assert main(["weather","nv",str(YEAR),"-q"]) == 0
    assert capsys.readouterr().out.strip() == f"NV {YEAR}: 17 added"
    assert main(["weather","NV",str(YEAR),"--refresh","-q"]) == 0
    assert "17 refreshed" in capsys.readouterr().out

def test_cli_errors(setup,capsys):
    """Bad arguments give a one-line error and exit code 1"""
    assert main(["weather","NY",str(YEAR)]) == 1
    assert "not a WECC state" in capsys.readouterr().err
    with pytest.raises(SystemExit) as err:
        main(["weather","NV"])
    assert err.value.code != 0
