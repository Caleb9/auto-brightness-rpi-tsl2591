import adafruit_tsl2591
import collections
import logging
import numpy
import re
import subprocess
import sys
import time


def execute_os_command(command: str) -> str:
    with subprocess.Popen(command.split(),
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          universal_newlines=True) as popen:
        error = popen.stderr.readline()
        if error != "":
            raise Exception(error)
        return popen.stdout.readline()


class Display:
    def __init__(self,
                 brightness_feature_code: str = "10",
                 dry_run: bool = False):
        self._brightness_feature_code = brightness_feature_code
        self._dry_run = dry_run
        self._getvcp_pattern = re.compile(f"^VCP {brightness_feature_code} C \d+ \d+")

    def set_brightness(self,
                       brightness: int) -> None:
        if not self._dry_run:
            execute_os_command(f"ddcutil setvcp {self._brightness_feature_code} {brightness}")
            logging.info(f"Set brightness to {brightness}")

    def get_brightness(self) -> (int, int):
        try:
            output = execute_os_command(f"ddcutil --brief getvcp {self._brightness_feature_code}")
            if not self._getvcp_pattern.match(output):
                print(
                    f"Invalid brightness feature VCP code {self._brightness_feature_code}."
                    " Find correct value with `ddcutil capabilities`.")
                sys.exit(1)
            # Example output "VCP 10 C 50 100", 50 is the current value, 100 is the max value
            brightness_value, max_brightness = str.split(output)[3:]
            return int(brightness_value), int(max_brightness)
        except Exception as error:
            error_message = error.args[0]
            if error_message.startswith("Display not found"):
                print(
                    "Your display does not seem to be supported by ddcutil. There's nothing you can do aside from "
                    "trying with a different monitor.")
                sys.exit(1)
            else:
                raise


class BrightnessSensor:
    def __init__(self,
                 sensor: adafruit_tsl2591.TSL2591,
                 max_brightness: int = 100):
        self._sensor = sensor
        self._max_brightness = max_brightness

    def get_brightness(self) -> int:
        # Visible-only levels range from 0-2147483647 (32-bit)
        visible = self._sensor.visible
        brightness = self._visible_to_brightness(visible)
        logging.info(f"Visible light: {visible}\tBrightness: {brightness}")
        return brightness

    def _visible_to_brightness(self,
                               visible: int) -> int:
        uint_32bit_max = 2147483647
        brightness = numpy.interp(visible, [0, uint_32bit_max], [0, self._max_brightness])
        brightness = round(brightness, 0)
        return int(brightness)


class BrightnessMeasurements:
    def __init__(self,
                 capacity: int = 10):
        self._deque = collections.deque(maxlen=capacity)

    def append_brightness(self,
                          brightness: int) -> None:
        self._deque.append(brightness)

    def get_average_brightness(self) -> int:
        return int(round(numpy.mean(self._deque), 0))


class BrightnessController:
    def __init__(self,
                 sensor: BrightnessSensor,
                 display: Display,
                 interval_seconds: int = 1):
        self._sensor = sensor
        self._display = display
        self._interval_seconds = interval_seconds

    def set_brightness_loop(self) -> None:
        prev_brightness = self._initialize_brightness()
        measurements = BrightnessMeasurements()
        measurements.append_brightness(prev_brightness)
        while True:
            time.sleep(self._interval_seconds)
            measurements.append_brightness(self._sensor.get_brightness())
            average_brightness = measurements.get_average_brightness()
            if average_brightness is not prev_brightness:
                self._display.set_brightness(average_brightness)
            prev_brightness = average_brightness

    def _initialize_brightness(self) -> int:
        initial_brightness = self._sensor.get_brightness()
        self._display.set_brightness(initial_brightness)
        return initial_brightness
