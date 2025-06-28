#!/usr/bin/env bash
set -euo pipefail

# container.pytest.bash invokes a `pytest` command in a "frontend" container.
# The container and a database server must be running before running this
# script (see README.md).
#
# Usage:
#    scripts/container.pytest.bash    # run all tests; continue after failures
#    scripts/container.pytest.bash -x # stop after first failure

# The command being invoked does not need to be quoted, unless it contains
# shell meta-characters or similar. Multiple words are fine, without quotes.
command=$*

# Change to the directory above the directory containing this script.
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )/.."

./scripts/container.exec.bash pytest "$command"
