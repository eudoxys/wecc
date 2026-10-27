#!/bin/bash
#
# This script updates the wecc repo based on the cache in the current venv
#

if [ -z "$VIRTUAL_ENV" ]; then
	echo "ERROR: no python venv" > /dev/stderr
	exit 1
fi

if [ "$1" == "--dryrun" ]; then
	GIT="echo git"
	COPY="echo cp"
else
	GIT="git"
	COPY="cp"
fi

PYTHON_VERSION=$(python --version | cut -f2 -d' ' | cut -f-2 -d'.')
CACHE_VERSION=$(python3 -c "import weather;print(weather.weather._version)")

# update weather
$GIT switch -c update-weather
$GIT push --set-upstream origin update-weather
WECC="AZ CA CO ID MT NM NV OR SD TX UT WA WY"
for STATE in $WECC; do
	for COUNTY in `find $VIRTUAL_ENV/lib/python$PYTHON_VERSION/site-packages/cache/.cache/weather/$CACHE_VERSION/$STATE -maxdepth 1 -type d -print`; do
		echo "Processing $(basename $COUNTY) $STATE..."
		FOUND=0
		for FILE in `find $COUNTY -maxdepth 1 -type f -print`; do
			LOCAL=wecc/weather/$STATE/$(basename $COUNTY)/$(basename $FILE)
			if ( ! test -f $LOCAL || ! diff $FILE $LOCAL 1>/dev/null 2>&1 ); then
				$COPY "$FILE" "$LOCAL"
				$GIT add "$LOCAL"
				FOUND=$(($FOUND + 1))
			fi
		done
		if [ $FOUND -gt 0 ]; then
			$GIT commit -m "Updating $(basename $COUNTY) $STATE"
			$GIT push origin
		fi
	done
done
