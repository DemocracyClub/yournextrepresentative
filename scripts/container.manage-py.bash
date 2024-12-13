#!/usr/bin/env bash
set -euo pipefail

# container.manage-py.bash invokes a Django management command in a frontend
# container, which must have been started beforehand.
#
# Usage:
#     scripts/container.manage-py.bash check

# The management command does not need to be quoted, unless it contains shell
# meta-characters. Multiple words are fine.
mgmtCommand="$@"

# Change to the directory above the directory containing this script.
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )/.."

./scripts/container.exec.bash python manage.py $mgmtCommand
