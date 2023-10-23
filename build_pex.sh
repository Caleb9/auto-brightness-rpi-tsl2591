# Builds pex package

set -x
python -m venv --upgrade-deps venv
. venv/bin/activate
pip install -U pex
make
