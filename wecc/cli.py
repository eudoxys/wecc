"""Command line interface

See `wecc` for the command syntax.

Examples
--------

    wecc print ...

outputs

    (real output)
"""

import sys
import argparse
import logging
import warnings

_logger = logging.getLogger(__file__)

def main(argv:list[str]|None=None) -> int:
    """Command line entry point

    Arguments
    ---------

      - `argv`: command line arguments (default `sys.argv[1:]`)

    Returns
    -------

      - `int`: exit code (0 on success)
    """
    parser = argparse.ArgumentParser(prog="wecc",
        epilog="See https://www.eudoxys.com/wecc for full documentation.")
    parser.add_argument("command",choices=["print"])
    parser.add_argument("--version",action="version",version=f"%(prog)s {sys.modules[__package__].__version__}")
    parser.add_argument("-d","--debug",action="store_true",help="enable debug logging and traceback on exceptions")
    parser.add_argument("-w","--warning",action="store_true",help="enable warning messages from python")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING)
    if not args.warning:
        warnings.simplefilter("ignore")

    try:
        # dispatch on args.command here
        return 0
    except Exception as err: # pylint: disable=broad-exception-caught
        if args.debug:
            raise
        print(f"ERROR [wecc]: {err}",file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
