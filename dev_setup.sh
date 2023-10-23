# Sets up development environment

set -x
python -m venv --upgrade-deps venv
. venv/bin/activate
pip install -r requirements/dev.txt
