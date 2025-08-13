#!/usr/bin/env bash
set -euo pipefail

# container.exec.bash invokes a command in a "frontend" container.
# The container must be running before running this script (see README.md).

# Note that the AWS-hosted environments do not have a container called
# "frontend"; this script is likely only of use with local development.
# For AWS command invocation, see the command called scripts/aws-container-exec.sh
#
# Usage:
#    scripts/container.exec.bash echo hello world
#
# This script is a deliberately simple convenience shim, and doesn't include a
# way to set or override environment variables. To do this, invoke "podman"
# directly:
#     podman compose exec -e key1=val -e key2=val frontend command param1 param2
# Updating variables held in env/frontend.env has no effect until the running
# container is restarted.

# The command being invoked does not need to be quoted, unless it contains
# shell meta-characters or similar. Multiple words are fine, without quotes.
cmd=("$@")

# Change to the directory above the directory containing this script.
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )/.."

podman compose exec frontend "${cmd[@]}"
