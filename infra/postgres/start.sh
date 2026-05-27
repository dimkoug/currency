#!/usr/bin/env bash
# Compute tuning flags from the container's resources, then hand off to the
# stock Postgres entrypoint so initdb / first-run logic still runs.
set -e
ARGS=$(/usr/local/bin/tune.sh)
exec docker-entrypoint.sh postgres $ARGS
