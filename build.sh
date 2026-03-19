#!/usr/bin/env bash
set -euo pipefail

CLEAN=0
TEST=0
INSTALL=0
PUBLISH="none"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean)
      CLEAN=1
      shift
      ;;
    --test)
      TEST=1
      shift
      ;;
    --install)
      INSTALL=1
      shift
      ;;
    --publish)
      PUBLISH="${2:-}"
      if [[ "$PUBLISH" != "none" && "$PUBLISH" != "testpypi" && "$PUBLISH" != "pypi" ]]; then
        echo "Invalid value for --publish: $PUBLISH"
        echo "Allowed values: none, testpypi, pypi"
        exit 1
      fi
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      echo "Usage: ./build.sh [--clean] [--test] [--install] [--publish none|testpypi|pypi]"
      exit 1
      ;;
  esac
done

step() {
  echo "==> $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON_CMD" ]]; then
  echo "Virtual environment not found. Run ./install.sh first."
  exit 1
fi

if [[ "$CLEAN" -eq 1 ]]; then
  step "Cleaning build artifacts"
  rm -rf "$SCRIPT_DIR/dist" "$SCRIPT_DIR/build"
  find "$SCRIPT_DIR" -maxdepth 1 -type d -name "*.egg-info" -exec rm -rf {} +
fi

step "Ensuring build tools"
"$PYTHON_CMD" -m pip install --upgrade pip build twine

if [[ "$INSTALL" -eq 1 ]]; then
  step "Installing package in editable mode"
  "$PYTHON_CMD" -m pip install -e .
fi

if [[ "$TEST" -eq 1 ]]; then
  step "Running tests"
  "$PYTHON_CMD" -m pytest
fi

step "Building sdist and wheel"
"$PYTHON_CMD" -m build

step "Checking distributions"
"$PYTHON_CMD" -m twine check "$SCRIPT_DIR"/dist/*

case "$PUBLISH" in
  testpypi)
    step "Uploading to TestPyPI"
    "$PYTHON_CMD" -m twine upload --repository testpypi "$SCRIPT_DIR"/dist/*
    ;;
  pypi)
    step "Uploading to PyPI"
    "$PYTHON_CMD" -m twine upload "$SCRIPT_DIR"/dist/*
    ;;
esac