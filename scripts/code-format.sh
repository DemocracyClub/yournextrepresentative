#!/bin/bash
set -euxo pipefail

uv run ruff format .
uv run ruff check . --fix
git ls-files '*.html' | xargs uv run djhtml
