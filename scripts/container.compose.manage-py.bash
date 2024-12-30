#!/usr/bin/env bash
set -euo pipefail

# container.compose.manage.bash invokes a Django management command in a new
# container, abiding by the invocation setup and bind mounts encoded in
# docker-compose.yml.
command="$1"

# Change to the directory above the directory containing this script.
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )/.."

podman compose run --rm --no-deps -e DJANGO_SETTINGS_MODULE=ynr.settings.testing frontend python manage.py $command
