"""Fast tests of `wecc.loads` and `wecc loads`

Builds by the `loads` package are replaced by synthetic data, so these tests
need neither `loads`, network, nor credentials. Files are written to a
temporary folder.
"""

import os
import gzip

import pandas as pd
import pytest

from wecc import loads
from wecc.cli import main

REFERENCE = loads.REFERENCE_YEAR # 2018: reference files and estimates
YEAR = 2020 # leap year: estimates only

def _hours(year):
    """Hourly UTC index of a year"""
    return pd.date_range(f"{year}-01-01",f"{year+1}-01-01",freq="1h",tz="UTC",inclusive="left",name="timestamp")

def _reference(state,county,refresh=False): # pylint: disable=unused-argument
    """Stand-in for `loads._reference` returning valid reference files"""
    frame = pd.DataFrame({"elec_baseload_MW":1.0,loads.ENDUSE:2.0},index=_hours(REFERENCE))
    text = frame.to_csv().encode()
    result = {x:text for x in loads.REFERENCE_FILES}
    result["RSD.csv.gz"] = b",bldg_id,out.electricity.total\n0,1,2.0\n"
    return result

def _estimate(state,county,year,harmonic,refresh=False): # pylint: disable=unused-argument
    """Stand-in for `loads._estimate` returning a valid hourly year"""
    return pd.DataFrame({loads.ENDUSE:1.0},index=_hours(year))

@pytest.fixture(name="setup")
def fixture_setup(tmp_path,monkeypatch):
    """Redirect output to a temporary folder and stub out the builds"""
    calls = []
    def reference(*args,**kwargs):
        calls.append(("reference",)+args)
        return _reference(*args,**kwargs)
    def estimate(*args,**kwargs):
        calls.append(("estimate",)+args)
        return _estimate(*args,**kwargs)
    monkeypatch.setattr(loads,"LOADSDIR",str(tmp_path))
    monkeypatch.setattr(loads,"_reference",reference)
    monkeypatch.setattr(loads,"_estimate",estimate)
    monkeypatch.setattr(loads._wecc_weather,"_check_credentials",lambda:None) # pylint: disable=protected-access
    return tmp_path,calls

def test_harmonics():
    """WECC counties get their medoid harmonics, others none"""
    assert loads.harmonics("OR","Lincoln") == [2,2,2]
    assert all(isinstance(x,int) for x in loads.harmonics("CA","Los Angeles"))
    assert loads.harmonics("TX","Harris") is None
    assert len([x for x in loads.counties("NV") if loads.harmonics("NV",x)]) == 17

def test_files():
    """Reference files only in the reference year; estimates only in WECC"""
    assert loads.files("NV","Clark",REFERENCE) == loads.REFERENCE_FILES + [f"Estimate_{REFERENCE}.csv.gz"]
    assert loads.files("NV","Clark",YEAR) == [f"Estimate_{YEAR}.csv.gz"]
    assert loads.files("TX","Harris",REFERENCE) == loads.REFERENCE_FILES
    assert not loads.files("TX","Harris",YEAR)

def test_pathname():
    """County folder names use underscores for spaces"""
    path = loads.pathname("CA","Los Angeles","R.csv.gz","/x")
    assert path == "/x/CA/Los_Angeles/R.csv.gz"

@pytest.mark.parametrize("state,year",[("NY",YEAR),("XX",YEAR),("NV",1990),("NV",2999)])
def test_bad_arguments(state,year,setup):
    """Non-WECC states and impossible years are rejected before any build"""
    with pytest.raises(ValueError):
        loads.update(state,year)
    assert not setup[1]

def test_reference_year(setup):
    """The reference year adds reference, building type and estimate files"""
    _,calls = setup
    result = loads.update("NV",REFERENCE)
    assert (result.status=="added").all() and len(result) == 17
    assert (result.files==5).all()
    for name in loads.REFERENCE_FILES + ["RSD.csv.gz",f"Estimate_{REFERENCE}.csv.gz"]:
        assert os.path.exists(loads.pathname("NV","White Pine",name))
    data = pd.read_csv(loads.pathname("NV","White Pine",f"Estimate_{REFERENCE}.csv.gz"),
        index_col=["timestamp"],parse_dates=["timestamp"])
    assert list(data.columns) == [loads.ENDUSE] and len(data) == 8760
    assert len(calls) == 34

def test_add_then_skip_then_refresh(setup):
    """Missing files are added, existing ones kept unless refreshed"""
    folder,calls = setup
    result = loads.update("NV",YEAR)
    assert (result.status=="added").all() and (result.files==1).all()
    path = loads.pathname("NV","White Pine",f"Estimate_{YEAR}.csv.gz")
    data = pd.read_csv(path,index_col=["timestamp"],parse_dates=["timestamp"])
    assert len(data) == 8784 and not os.path.exists(loads.pathname("NV","White Pine","R.csv.gz"))
    with open(path,"rb") as fh:
        before = fh.read()

    calls.clear()
    result = loads.update("NV",YEAR)
    assert (result.status=="unchanged").all() and not calls

    result = loads.update("NV",YEAR,refresh=True)
    assert (result.status=="refreshed").all() and len(calls) == 17
    with open(path,"rb") as fh:
        assert fh.read() == before, "identical data must give identical bytes"
    assert not [x for x in os.listdir(os.path.dirname(path)) if x.endswith(".tmp")]
    assert str(folder) in path

def test_missing_file_only(setup):
    """Without refresh only the missing files of a county are written"""
    loads.update("NV",REFERENCE)
    os.remove(loads.pathname("NV","Clark","C.csv.gz"))
    result = loads.update("NV",REFERENCE)
    assert result.loc["Clark","status"] == "added" and result.loc["Clark","files"] == 1
    assert (result.drop("Clark").status=="unchanged").all()

def test_non_wecc_counties_skipped(setup):
    """Counties outside WECC get reference data but no estimate"""
    _,calls = setup
    result = loads.update("TX",YEAR)
    assert (result.status=="skipped").sum() == len(result) - (result.status=="added").sum()
    assert 0 < (result.status=="added").sum() < 254
    assert all(x[0] == "estimate" for x in calls)
    result = loads.update("TX",REFERENCE)
    assert result.loc["Harris","status"] == "added" and result.loc["Harris","files"] == 4

def test_failure_keeps_file(setup,monkeypatch):
    """A failed or invalid build is reported and leaves existing files intact"""
    loads.update("NV",YEAR)
    path = loads.pathname("NV","Clark",f"Estimate_{YEAR}.csv.gz")
    def bad(state,county,year,harmonic,refresh=False):
        if county == "Clark":
            return _estimate(state,county,year,harmonic).iloc[:-1] # one hour short
        if county == "Washoe":
            data = _estimate(state,county,year,harmonic)
            data.iloc[5,0] = float("nan")
            return data
        raise RuntimeError("build failed")
    monkeypatch.setattr(loads,"_estimate",bad)
    result = loads.update("NV",YEAR,refresh=True)
    assert (result.status=="failed").all()
    assert "missing" in result.loc["Washoe","message"]
    with gzip.open(path,"rt") as fh:
        assert len(fh.readlines()) == 8785

def test_bad_reference(setup,monkeypatch):
    """Reference files that break the contract are not written"""
    def bad(state,county,refresh=False):
        result = _reference(state,county,refresh)
        result["R.csv.gz"] = b"timestamp,elec_total_MW\n2018-01-01 00:00:00+00:00,1.0\n"
        return result
    monkeypatch.setattr(loads,"_reference",bad)
    result = loads.update("NV",REFERENCE)
    assert (result.status=="failed").all()
    assert not os.path.exists(loads.pathname("NV","Clark","R.csv.gz"))

def test_cachefile(tmp_path,monkeypatch):
    """Cached files are found in the latest cache version"""
    from cache import Cache # pylint: disable=import-outside-toplevel
    monkeypatch.setattr(Cache,"CACHEDIR",str(tmp_path))
    for version in ["0","2","10"]:
        os.makedirs(tmp_path/"loads"/version/"NV"/"Clark")
        (tmp_path/"loads"/version/"NV"/"Clark"/"C.csv.gz").write_bytes(b"")
    path = loads._cachefile("NV","Clark","C.csv.gz") # pylint: disable=protected-access
    assert path == str(tmp_path/"loads"/"10"/"NV"/"Clark"/"C.csv.gz")
    assert loads._cachefile("NV","Clark","R.csv.gz") is None # pylint: disable=protected-access

def test_missing_credentials(tmp_path,monkeypatch):
    """Builds without credentials fail with a clear message"""
    monkeypatch.setattr(loads,"LOADSDIR",str(tmp_path))
    monkeypatch.setenv("HOME",str(tmp_path))
    with pytest.raises(RuntimeError,match="weather register"):
        loads.update("NV",YEAR)

def test_cli(setup,capsys):
    """`wecc loads STATE YEAR` updates the state and summarizes"""
    assert main(["loads","nv",str(YEAR),"-q"]) == 0
    assert capsys.readouterr().out.strip() == f"NV {YEAR}: 17 added"
    assert main(["loads","NV",str(YEAR),"--refresh","-q"]) == 0
    assert "17 refreshed" in capsys.readouterr().out

def test_cli_errors(setup,capsys,monkeypatch):
    """Bad arguments and failed counties give errors and exit code 1"""
    assert main(["loads","NY",str(YEAR)]) == 1
    assert "not a WECC state" in capsys.readouterr().err
    with pytest.raises(SystemExit) as err:
        main(["loads","NV"])
    assert err.value.code != 0
    def bad(*args,**kwargs):
        raise RuntimeError("build failed")
    monkeypatch.setattr(loads,"_estimate",bad)
    assert main(["loads","NV",str(YEAR),"-q"]) == 1
    assert "ERROR [wecc]: NV Clark 2020: build failed" in capsys.readouterr().err
