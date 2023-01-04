"""
Command-line script to interface with an Aranet4 CO₂ meter
"""
import datetime
import argparse
import requests
import time
import csv
import io
import re

from pyaranet4 import Aranet4


def main():
    """
    pyaranet4 Command-line interface
    """
    cli = argparse.ArgumentParser(add_help=False)
    cli.add_argument("--help", help="Show this help message and exit", default=False, action="help")
    cli.add_argument("--history", "-h", help="Retrieve historical readings saved on device", default=False,
                     action="store_true")
    cli.add_argument("--history-start", "-hs",
                     help="Start of range of historical readings to retrieve, inclusive, as UTC timestamp (2019-09-29T14:00:00Z)")
    cli.add_argument("--history-end", "-he",
                     help="End of range of historical readings to retrieve, inclusive, as UTC timestamp (2019-09-29T14:00:00Z)")
    cli.add_argument("--output-file", "-o",
                     help="Save retrieved historical readings to file as CSV (implies --history)")
    cli.add_argument("--limit", "-l",
                     help="Get <value> most recent historical values (implies --history, ignores --history-start and --history-end)",
                     type=int, default=0)
    cli.add_argument("--url", "-u", help="Send current values to this URL as a POST request (ignores --history)")
    cli.add_argument("--params", "-p", default="thpc",
                     help="Sensors to read from, as a combination of (t)emperature, (h)umidity, (p)ressure, (c)o2, default thpc, implies --history")
    cli.add_argument("address", nargs="*", action="extend",
                     help="MAC address of Aranet4 device to connect to. If left empty, use autodiscovery.")
    args = cli.parse_args()

    if not args.address:
        args.address = None

    a4 = Aranet4(args.address)
    if args.url:
        post_data(a4, args.url)
        exit(0)

    elif args.history or args.limit or args.output_file:
        # Map "thpc"-like sensor value as provided to actual sensor IDs
        sensor_map = {"t": a4.SENSOR_TEMPERATURE, "h": a4.SENSOR_HUMIDITY, "p": a4.SENSOR_PRESSURE,
                      "c": a4.SENSOR_CO2}
        sensors = tuple([sensor_map[c] for c in re.sub(r"[^thpc]", "", args.params)])
        if not sensors:
            print("Must include at least one valid sensor")
            exit(1)

        collect_data(a4, args, sensors)
        exit(0)

    # If no parameters are given, simply display a short summary of the current
    # settings and readings.
    basic_overview(a4)
    exit(0)


def basic_overview(a4):
    """
    Display a basic sensor and settings overview

    :param Aranet4 a4:  Aranet4 device object to read from
    """
    print("--------------------------------------")
    print("Connected: {:s} | {:s}".format(a4.device_name, a4.software_revision))
    print("Updated {:d} s ago. Intervals: {:d} s".format(a4.since_last_update, a4.update_interval))
    print("{:d} total readings".format(a4.stored_readings_amount))
    print("--------------------------------------")
    print("CO2:         {:d} ppm".format(a4.current_readings.co2))
    print("Temperature: {:.2f} C".format(a4.current_readings.temperature))
    print("Humidity:    {:d} %".format(a4.current_readings.humidity))
    print("Pressure:    {:.2f} hPa".format(a4.current_readings.pressure))
    print("Battery:     {:d} %".format(a4.current_readings.battery_level))
    print("--------------------------------------")
    exit()


def post_data(a4, url):
    """
    Send current values to this URL as a POST request (ignores --history)

    :param Aranet4 a4:  Aranet4 device object to read from
    :param str url:  URL to POST data to
    """
    age = a4.since_last_update
    values = a4.current_readings
    r = requests.post(url, data={
        'time': time.time() - age,
        'co2': values.co2,
        'temperature': values.temperature,
        'pressure': values.pressure,
        'humidity': values.humidity,
        'battery': values.battery_level
    })


def collect_data(a4, args, sensors):
    """
    Fetch and aggregate historical readings

    :param Aranet4 a4:  Aranet4 device object to read from
    :param args:  Command-line arguments
    :param tuple sensors:  Sensor IDs to include in readings
    """
    # Fetch history. It will take a while to fetch anyway, so just get everything
    # and filter afterwards according to parameters.
    history = a4.get_history(sensors)
    out_stream = io.StringIO() if not args.output_file else open(args.output, "w")

    writer = csv.DictWriter(out_stream, fieldnames=("index", "timestamp", *history.sensors))
    writer.writeheader()

    # We're working with Unix timestamps, so convert provided range first
    range_start = datetime.datetime.strptime(args.history_start,
                                             "%Y-%m-%dT%H:%M:%SZ").timestamp() if args.history_start else None
    range_end = datetime.datetime.strptime(args.history_end,
                                           "%Y-%m-%dT%H:%M:%SZ").timestamp() if args.history_end else None

    # Go through history - we implement the --limit parameter here
    for index in list(history.__getattribute__(history.sensors[0]).keys())[-args.limit:]:
        # and the date range (if provided) here
        if range_start and range_start > history.timestamps[index]:
            continue

        if range_end and range_end < history.timestamps[index]:
            continue

        # CSV row - only requested sensors are included as columns
        writer.writerow({
            "index": index,
            "timestamp": datetime.datetime.fromtimestamp(history.timestamps[index]).strftime("%Y-%m-%d %H:%M:%S"),
            **{
                sensor: history.__getattribute__(sensor)[index] for sensor in history.sensors
            }
        })

    # Either save the CSV to a file, or send it to the output buffer
    if args.output_file:
        out_stream.close()
    else:
        print(out_stream.getvalue())


if __name__ == "__main__":
    main()
