"""Shared test setup

Set `{{{PACKAGE_UPPER}}}_CACHEDIR` to keep downloaded data in a folder other than the
`cache` package default (inside site-packages, so lost on every fresh
install, e.g., in CI).
"""

import os

try:
    from cache import Cache
except ImportError: # this package does not use the Eudoxys cache
    Cache = None

if Cache is not None and os.environ.get("{{{PACKAGE_UPPER}}}_CACHEDIR"):
    Cache.CACHEDIR = os.environ["{{{PACKAGE_UPPER}}}_CACHEDIR"]
