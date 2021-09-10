# pyaranet4 - Interface with your Aranet4 CO₂ meter via Python

[![PyPI version](https://img.shields.io/pypi/v/pyaranet4.svg?logo=pypi&logoColor=FFE873)](https://pypi.org/project/prettytable/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/pyaranet4.svg?logo=python&logoColor=FFE873)](https://pypi.org/project/pyaranet4/)

This is a cross-platform interface for the [Aranet4](https://aranet4.com/) CO₂ meter. You can use it to  read values 
from the meter to then store in a database, display on a website, or generally do with whatever you want. Since the 
official mobile app for the device does not have automatic export features and the manual export is prone to failure, 
you can use this library instead for such purposes.

It is built with [Bleak](https://github.com/hbldh/bleak), a cross-platform Python Bluetooth client. It is also 
heavily inspired by [Aranet4-Python](https://github.com/Anrijs/Aranet4-Python), an excellent library that is 
unfortunately only compatible with Linux.

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

You can find the full API documentation [here](/).