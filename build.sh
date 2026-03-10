#!/bin/zsh
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest
python -m build
python -m twine check dist/*
python -m pip uninstall -y hudu-magic
python -m pip install -e '.[dev]'
find src -maxdepth 2 -type f | sort
python -c "import sys; print(sys.executable)"
python -c "import site; print(site.getsitepackages())"
python -c "import hudu_magic"