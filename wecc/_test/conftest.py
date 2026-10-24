"""Shared test setup

Set `WECC_CACHEDIR` to keep downloaded data in a folder other than the
`cache` package default (inside site-packages, so lost on every fresh
install, e.g., in CI).
"""

import os

try:
    from cache import Cache
except ImportError: # this package does not use the Eudoxys cache
    Cache = None

if Cache is not None and os.environ.get("WECC_CACHEDIR"):
    Cache.CACHEDIR = os.environ["WECC_CACHEDIR"]
