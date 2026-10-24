"""Fast tests of the package import and command line interface"""

import pytest

import {{{PACKAGE}}}
from {{{PACKAGE}}}.cli import main

def test_version():
    """The package reports a version string"""
    assert isinstance({{{PACKAGE}}}.__version__,str) and {{{PACKAGE}}}.__version__

@pytest.mark.parametrize("option",["--help","--version"])
def test_info_options(option,capsys):
    """`--help` and `--version` print to stdout and exit with code 0"""
    with pytest.raises(SystemExit) as err:
        main([option])
    assert err.value.code == 0
    assert capsys.readouterr().out

def test_bad_command():
    """An unknown command exits with a nonzero code"""
    with pytest.raises(SystemExit) as err:
        main(["no-such-command"])
    assert err.value.code != 0
