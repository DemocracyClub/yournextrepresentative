#!/usr/bin/env bash
set -xeuo pipefail

# container.image.build.bash builds an image from a stage defined in
# container/build/Containerfile, and tags it as "ynr:$image".
image="$1"; shift
args=("$@")

# Change to the directory above the directory containing this script.
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )/.."

# Choose a build tool.
# CircleCI uses docker; others (e.g. developers) use podman.
set +u; if [[ "$CIRCLECI" == "true" ]]; then
  builder="docker"
else
  builder="podman"
fi; set -u

# Build the image.
"$builder" build --target "$image" --tag "ynr:$image" -f container/build/Containerfile "${args[@]}" .
