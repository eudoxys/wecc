"""Command line interface

See `wecc` for the command syntax.

Examples
--------

    wecc weather NV 2023

adds any missing 2023 weather files for the Nevada counties, reporting each
county as it goes, then a summary such as

    NV 2023: 17 added

See `wecc.weather` for details.
"""

import sys
import argparse
import logging
import warnings

_logger = logging.getLogger(__file__)

def _common() -> argparse.ArgumentParser:
    """@private Options accepted both before and after the command"""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-d","--debug",action="store_true",default=argparse.SUPPRESS,
        help="enable debug logging and traceback on exceptions")
    common.add_argument("-w","--warning",action="store_true",default=argparse.SUPPRESS,
        help="enable warning messages from python")
    return common

def main(argv:list[str]|None=None) -> int:
    """Command line entry point

    Arguments
    ---------

      - `argv`: command line arguments (default `sys.argv[1:]`)

    Returns
    -------

      - `int`: exit code (0 on success, 1 on failure, including any county
        that failed to update)
    """
    common = _common()
    parser = argparse.ArgumentParser(prog="wecc",parents=[common],
        epilog="See https://www.eudoxys.com/wecc for full documentation.")
    parser.add_argument("--version",action="version",version=f"%(prog)s {sys.modules[__package__].__version__}")
    commands = parser.add_subparsers(dest="command",required=True,metavar="COMMAND")

    weather = commands.add_parser("weather",parents=[common],
        help="add or refresh county weather data for a WECC state and year",
        description="Add or refresh the county weather files wecc/weather/STATE/COUNTY/W_YEAR.csv.gz")
    weather.add_argument("state",type=str.upper,help="WECC state abbreviation, e.g., CA")
    weather.add_argument("year",type=int,help="weather year, e.g., 2023")
    weather.add_argument("-r","--refresh",action="store_true",
        help="download and rewrite files that already exist")
    weather.add_argument("-q","--quiet",action="store_true",
        help="do not report progress per county")

    args = parser.parse_args(argv)
    debug = getattr(args,"debug",False)

    logging.basicConfig(level=logging.DEBUG if debug else logging.WARNING,format="%(message)s")
    if not getattr(args,"warning",False):
        warnings.simplefilter("ignore")

    try:

        match args.command:

            case "weather":

                from wecc import weather as wecc_weather # pylint: disable=import-outside-toplevel
                if not args.quiet and not debug:
                    logging.getLogger(wecc_weather.__file__).setLevel(logging.INFO)
                summary = wecc_weather.update(args.state,args.year,refresh=args.refresh)
                counts = summary.status.value_counts()
                print(f"{args.state} {args.year}: "
                    + ", ".join(f"{counts[x]} {x}" for x in wecc_weather.STATUS if x in counts))
                failed = summary[summary.status=="failed"]
                for county,row in failed.iterrows():
                    print(f"ERROR [wecc]: {args.state} {county} {args.year}: {row.message}",file=sys.stderr)
                return 1 if len(failed) else 0

        raise ValueError(f"command {args.command} not implemented")

    except Exception as err: # pylint: disable=broad-exception-caught
        if debug:
            raise
        print(f"ERROR [wecc]: {err}",file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
