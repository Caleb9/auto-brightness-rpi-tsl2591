# Needed by pex

from distutils.core import setup

setup(
    name="auto-brightness-rpi-tsl2591",
    version="0.0.0",
    py_modules=["brightness"],
    scripts=["main.py"],
)
