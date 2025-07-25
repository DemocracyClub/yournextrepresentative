#!/usr/bin/env bash
set -euo pipefail

# container.run.bash invokes a command in a newly instantiated "frontend"
# container.
#
# The container and its filesystem are removed after the user's command exits.
# Only changes made inside bind-mounted filesystems are persisted (see
# docker-compose.yml for a list of bind mounts). The database container must be
# running before this script can be invoked (see README.md) because the compose
# command sees the database as a required dependency. This is the case even if
# the command being executed doesn't use the database.
#
# Usage:
#    scripts/container.run.bash env
#
# Because a new container is instantiated along with its environment each time
# this script is invoked, the contents of the env/frontend.env file are
# respected for each invocation, with environment variables being set as per
# that file.

# The command being invoked does not need to be quoted, unless it contains
# shell meta-characters or similar. Multiple words are fine, without quotes.
command=$*

# Change to the directory above the directory containing this script.
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )/.."

podman compose run --rm --no-deps --name tmp-fe-$$ frontend "$command" \
  2> >( grep -v "Error: adding pod to state.*pod already exists" >&2 )
