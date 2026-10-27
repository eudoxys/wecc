#!/bin/bash
#
# This script update the wecc repo based on the cache in the current venv
#

ACTION=echo # echo for dry-run, nothing to take the action

if [ -z "$VIRTUAL_ENV" ]; then
	echo "ERROR: no python venv" > /dev/stderr
	exit 1
fi

PYTHON_VERSION=$(python --version | cut -f2 -d' ' | cut -f-2 -d'.')
CACHE_VERSION=$(python3 -c "import weather;print(weather.weather._version)")

# update weather
$ACTION git switch -c update-weather
WECC="AZ CA CO ID MT NM NV OR SD TZ UT WA WY"
for STATE in $WECC; do
	for COUNTY in `find $VIRTUAL_ENV/lib/python$PYTHON_VERSION/site-packages/cache/.cache/weather/$CACHE_VERSION/$STATE -maxdepth 1 -type d -print`; do
		echo "Processing $(basename $COUNTY) $STATE..."
		for FILE in `find $COUNTY -maxdepth 1 -type f -print`; do
			$ACTION git add "$FILE"
		done
		$ACTION git commit -m "Adding $(basename $COUNTY) $STATE"
		$ACTION git push
	done
done
