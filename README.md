# auto-brightness-rpi-tsl2591

Control monitor brightness to match ambient light with Raspberry Pi
and [TSL2591](https://www.adafruit.com/product/1980) lux sensor.


## What?

I wrote this code for a DIY [digital photo frame
project](https://github.com/Caleb9/synology-photos-slideshow) using
Raspberry Pi connected to a monitor. Based on the TSL2591 lux sensor
readings of visible ambient light, the app sets matching monitor
brightness.


## How Does It Work?

The code maps readings of TSL2591 sensor to detected monitor's
brightness scale. Underneath it uses
[ddcutil](https://www.ddcutil.com/) command to set the monitor's
brightness setting.

Ambient light is sampled once per second. Even though it's possible to
achieve stable lighting conditions with artificial light, a digital
photo frame most likely sits somewhere in your room where daylight can
reach it. Because daylight fluctuates constantly, the code does not
immediately set brightness to currently detected value to avoid
constant flickering of the brightness. Instead brightness is set to
the *average of the readings from last 10 seconds*. In relatively
stable lighting conditions this reduces the annoying flickering
effect. When lighting changes significantly (e.g. when you switched
light on in the room after dark), it takes around 10 seconds to
gradually reach the target value. I haven't tested the app with strobo
lights though.

Currently, the entire range of sensor's readings is mapped linearly to
monitor's brightness setting scale (usually 0-100). This approach is
rather naive, but seems to work well enough for the monitor I'm
using. I might think of implementing some kind of enveloping for the
values at some point though.


## Raspberry Pi Setup

### 0. Attaching TSL2591 to Raspberry Pi

See [the guide about wiring the sensor to Raspberry
Pi](https://learn.adafruit.com/adafruit-tsl2591/python-circuitpython#python-computer-wiring-2997855).


### 1. Install dependencies

The assumption is that you are starting with a fresh installation of
Raspberry Pi OS Lite and you have command line access to the Pi.

Update the system and install the OS packages needed

```
sudo apt install -y \
    python3-dev \
    python3-venv \
    ddcutil \
    git
```

`python3-dev` and `python3-venv` are needed to build the source code
into a stand-alone executable.  `ddcutil` is a command line tool to
set monitor's brightness. Git is optional, and only needed if you'll
be cloning the repository.


#### 32-bit System 

There are some extra steps needed when setting up a 32-bit system. You
can check if your system is 32 or 64-bit with `getconf LONG_BIT`
command.

You need to install an extra package to make numpy (one of the apps
dependencies) work:

```
sudo apt install libatlas-base-dev
```


### 2. Build and Test

Clone the repository using `git glone`, or download the source code
zip and extract e.g. to `/home/pi/auto-brightness-rpi-tsl2591`.

`cd` into the directory and run

```
./build_pex.sh
```

#### 32-bit System 

You need to prepend the `./build_pex.sh` with `CFLAGS=-fcommon`:

```
CFLAGS=-fcommon ./build_pex
```

Wait for the build to finish. A new file `auto-brightness-rpi-tsl2591.pex`
has been created.

Display help message:

```
./auto-brightness-rpi-tsl2591.pex --help
```

Test the app with:

```
./auto-brightness-rpi-tsl2591.pex --dry-run --verbose
```

By default, monitor's brightness VCP feature code is 10. Run `ddcutil
capabilities` to find out if it's the same on your monitor, e.g. this
is part of the output of `ddcutil capabilities` command:

```
...
VCP Features:
   Feature: 02 (New control value)
   Feature: 04 (Restore factory defaults)
   Feature: 05 (Restore factory brightness/contrast defaults)
   Feature: 08 (Restore color defaults)
   Feature: 09 (Brightness)
   Feature: 12 (Contrast)
...
```

In this case, we can see that the brightness feature code is 09. Add
`--vcp` option when executing:

```
./auto-brightness-rpi-tsl2591.pex --dry-run --verbose --vcp 09
```

If everything works fine you should see the output such as this, with
new value being printed every second:

```
[2023-02-01 11:46:40] INFO Initial brightness: 84
[2023-02-01 11:46:40] INFO Visible light: 1711512060    Brightness: 80
[2023-02-01 11:46:41] INFO Visible light: 1706531400    Brightness: 79
```

### Run

If testing went well, it's time to make the app actually change the
monitor brightness (remember to also set `--vcp` option if feature
code is different than 10):

```
./auto-brightness-rpi-tsl2591.pex --verbose
```

#### Fiddling With Sensor Settings

There's a plethora of different monitors out there and their actual
brightness settings differ greatly. If the brightness set by the app
does not suit your taste, you may try to modify the code in
[`main.py`](main.py) file, particularly the two lines setting gain and
integration time of the TSL2591 sensor:

```
   sensor.gain = adafruit_tsl2591.GAIN_HIGH
   sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_300MS
```

See [the description of the possible
values](https://learn.adafruit.com/adafruit-tsl2591/wiring-and-test#gain-and-timing-762936)
for details.

The values set in the code are corresponding to settings I found
working best with my particular monitor. I'm planning to add a command
line option for setting these in the future, so it's not necessary to
edit the code. For now, you can change the code in `main.py` and
re-build the app (`./build_pex.sh`).


### [Optional] Auto-Start

To start the brightness control automatically when Pi gets booted,
enable auto-login using `raspi-config` and add the following line to
`/etc/rc.local` just before `exit 0` (change path to match the
location of your file, also if your Pi username is different than
`pi`, change that as well):

```
su pi -c "/home/pi/auto-brightness-rpi-tsl2591/auto-brightness-rpi-tsl2591.pex &"
```
