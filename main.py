#!/usr/bin/env python3

import adafruit_tsl2591
import argparse
import board
import logging
import os
import shutil
import sys

import brightness


def check_environment() -> bool:
    if shutil.which("ddcutil") is None:
        print("Required command 'ddcutil' not found. Install with 'sudo apt install ddcutil'.")
        return False
    if shutil.which("raspi-config") is not None:
        with os.popen("raspi-config nonint get_i2c", "r") as stream:
            if stream.read() != "0\n":
                print("I2C port is disabled. Enable with 'sudo raspi-config nonint do_i2c 0'.")
                return False
    else:
        logging.warning("'raspi-config' command not found. If you're executing on something else than Raspberry Pi OS, "
                        "stuff will probably not work as expected. You're on your own.")
    return True


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose",
                        help="print brightness values to stdout",
                        action="store_true")
    parser.add_argument("--vcp",
                        help="set brightness feature code, use 'ddcutil capabilities' to find the value",
                        type=str,
                        default="10")
    parser.add_argument("--dry-run",
                        help="do not set brightness, combine with --verbose to only print detected brightness values",
                        action="store_true")
    return parser.parse_args()


def set_logging_level(verbose: bool):
    level = logging.WARNING
    if verbose:
        level = logging.INFO
    logging.basicConfig(format="[%(asctime)s] %(levelname)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S', level=level)


def main() -> None:
    args = parse_arguments()
    set_logging_level(args.verbose)

    if not check_environment():
        sys.exit(1)

    display = brightness.Display(args.vcp, args.dry_run)
    initial_brightness, max_brightness = display.get_brightness()
    logging.info(f"Initial brightness: {initial_brightness}")
    try:
        # Create sensor object, communicating over the board's default I2C bus
        i2c = board.I2C()  # uses board.SCL and board.SDA

        # Initialize the sensor.
        sensor = adafruit_tsl2591.TSL2591(i2c)

        sensor.gain = adafruit_tsl2591.GAIN_HIGH
        sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_300MS

        brightness_controller = \
            brightness.BrightnessController(
                brightness.BrightnessSensor(sensor, max_brightness),
                display)
        brightness_controller.set_brightness_loop()
    except KeyboardInterrupt:
        pass
    finally:
        display.set_brightness(initial_brightness)


if __name__ == "__main__":
    main()
