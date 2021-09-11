# pyaranet4 - Interface with your Aranet4 CO₂ meter via Python

[![PyPI version](https://img.shields.io/pypi/v/pyaranet4?logo=pypi&logoColor=FFE873)](https://pypi.org/project/pyaranet4/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/pyaranet4?logo=python&logoColor=FFE873)](https://pypi.org/project/pyaranet4/)

This is a cross-platform interface for the [Aranet4](https://aranet4.com/) CO₂ meter. You can use it to read values from
the meter to then store in a database, display on a website, or generally do with whatever you want. Since the official
mobile app for the device does not have automatic export features and the manual export is prone to failure, you can use
this library instead for such purposes.

It is built with [Bleak](https://github.com/hbldh/bleak), a cross-platform Python Bluetooth client. It is also heavily
inspired by [Aranet4-Python](https://github.com/Anrijs/Aranet4-Python), an excellent library that is unfortunately only
compatible with Linux.

* Works on MacOS, Linux and Windows
* Command-line tool and Python library
* Lightweight: instantiate class, read class properties, done

## Installation

```
pip install pyaranet4
```

## Usage

Before you do anything, make sure the device is properly paired. Once it is paired, pyaranet4 will usually be able to
figure out the rest (e.g. the MAC address) by itself. Note that Bluetooth LE is a slow protocol, and most commands and
calls will take a couple of seconds to complete. This is not an issue with the library, but a limitation of the
technology.

### As a command-line tool

pyaranet4 comes with a command-line utility, which is mostly compatible with Aranet4-Python's:

```
C:\> pyaranet4
--------------------------------------
Connected: Aranet4 06CDC | v0.4.4
Updated 56 s ago. Intervals: 60 s
2167 total readings
--------------------------------------
CO2:         511 ppm
Temperature: 25.05 C
Humidity:    58 %
Pressure:    1014.50 hPa
Battery:     98 %
--------------------------------------
```

Get stored historical values from the device:

```
C:\> pyaranet4 --history
index,timestamp,temperature,humidity,pressure,co2
1,2021-09-09 22:12:20,25.1,56,1014.5,584
2,2021-09-09 22:13:20,25.1,56,1014.5,590
3,2021-09-09 22:14:20,25.1,56,1014.5,579
...
```

Or save them to a file:

```
C:\> pyaranet4 --history --output-file=readings.csv
```

Or view the full list of command-line arguments and parameters:

```
C:\> pyaranet4 --help
```

### As a library

You can also use pyaranet4 as a library:

```python
from pyaranet4 import Aranet4

a4 = Aranet4()
print("Battery level: %s%%" % a4.battery_level)
print("Current CO₂ level: %i ppm" % a4.current_readings.co2)
print("Stored CO2 values:")
print(a4.history.co2)
```

The `Aranet4` object has the following public properties and methods:

* `current_readings` (namespace): The current readings of the device's sensors, as a namespace with properties `co2` (
  integer), `temperature` (float) `pressure` (float), `humidity` (integer), `battery_level` (integer)
  , `update_interval` (integer), and `since_last_update` (integer)
* `current_readings_simple` (namespace):  Identical to `current_readings`, but without the `update_interval`
  and `since_last_update` properties; may be faster to request
* `history` (namespace):  Historical readings stored on the device, as a namespace with properties `co2`, `temperature`
  , `pressure`, `humidity`, `sensors`, and `timestamps`. The sensor values are dictionaries with the interval index as
  keys and the sensor reading as values. `sensors` is a tuple of sensors included in the result. `timestamps` is a
  dictionary with indexes as keys and corresponding UNIX timestamps as values. The latter can be used to determine what
  the timestamp of a given value is.
* `mac_address` (string): The MAC address of the Bluetooth device
* `battery_level` (integer): Battery level, 0-100.
* `manufacturer_name` (string): The manufacturer of the device, e.g. `SAF Tehnika`
* `model_name` (string): The name of the device model, e.g. `Aranet4`
* `device_name` (string):  The name of the device, e.g. `Aranet4 06CDC`
* `hardware_revision` (integer): Hardware revision number, e.g. `9`
* `software_revision` (string): Software (firmware) version, e.g. `v0.4.4`
* `update_interval` (integer): Amount of seconds between sensor updates
* `since_last_update` (integer): Amount of seconds since last sensor update
* `stored_readings_amount` (integer): Amount of sensor readings stored on the device
* `get_history(sensors: tuple, start: int, end: int)` (namespace): Same return type as `history`, but allows one to
  limit results to a given tuple of sensors and a given range of indexes, which can be faster to receive than the full
  history. Sensors should be a tuple of a combination of `Aranet4.SENSOR_CO2`, `Aranet4.SENSOR_HUMIDITY`, and so on.