all:
	pex . -r requirements/common.txt -c main.py -o auto-brightness-rpi-tsl2591.pex

requirements:
	pip-compile --resolver=backtracking --output-file=- requirements/common.in > requirements/common.txt && \
	pip-compile --resolver=backtracking --output-file=- requirements/dev.in > requirements/dev.txt
