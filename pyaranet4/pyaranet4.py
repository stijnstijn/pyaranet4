"""
Base class for a Bluetooth client for the Aranet4 CO₂ meter.
"""
import datetime
import logging
import asyncio
import time

from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError
from types import SimpleNamespace

from pyaranet4.util import le16, write_le16
from pyaranet4.exceptions import Aranet4NotFoundException, Aranet4BusyException, Aranet4UnpairedException


class Aranet4:
    """
    A class to read data with from an Aranet4 CO₂ meter.

    When instantiated, the object provides a set of properties that can be
    read to get readings, settings and historical data.
    """
    _address = None
    _cache = {}
    _use_cache = False
    _client = None
    _last_notification = 0
    _reading = False
    _magic = None

    # UUIDs of supported device characteristics
    UUID_BATTERY_LEVEL = "00002a19-0000-1000-8000-00805f9b34fb"
    UUID_MANUFACTURER_NAME = "00002a29-0000-1000-8000-00805f9b34fb"
    UUID_MODEL_NAME = "00002a24-0000-1000-8000-00805f9b34fb"
    UUID_DEVICE_NAME = "00002a00-0000-1000-8000-00805f9b34fb"
    UUID_SERIAL_NUMBER = "00002a25-0000-1000-8000-00805f9b34fb"
    UUID_HARDWARE_REVISION = "00002a27-0000-1000-8000-00805f9b34fb"
    UUID_SOFTWARE_REVISION = "00002a28-0000-1000-8000-00805f9b34fb"
    UUID_UPDATE_INTERVAL = "f0cd2002-95da-4f4b-9ac8-aa55d312af0c"
    UUID_SINCE_LAST_UPDATE = "f0cd2004-95da-4f4b-9ac8-aa55d312af0c"
    UUID_STORED_READINGS = "f0cd2001-95da-4f4b-9ac8-aa55d312af0c"
    UUID_CURRENT_READING_SIMPLE = "f0cd1503-95da-4f4b-9ac8-aa55d312af0c"
    UUID_CURRENT_READING_FULL = "f0cd3001-95da-4f4b-9ac8-aa55d312af0c"
    UUID_HISTORY_RANGE = "f0cd1402-95da-4f4b-9ac8-aa55d312af0c"
    UUID_HISTORY_NOTIFIER = "f0cd2003-95da-4f4b-9ac8-aa55d312af0c"

    # Available sensor identifiers
    SENSOR_TEMPERATURE = 1
    SENSOR_HUMIDITY = 2
    SENSOR_PRESSURE = 3
    SENSOR_CO2 = 4

    def __init__(self, mac_address=None, use_cache=False, magic_string="Aranet4"):
        """
        Set up Aranet4 object

        :param str mac_address:  Bluetooth MAC address to connect to. If left
        empty, `magic_string` is used to discover the Aranet4 device.
        :param bool use_cache:  Whether to cache retrieved data. Can be useful
        when using the object as part of a script that accesses values
        multiple times, since reading is quite slow.
        :param str magic_string:  String to look for in device names to
        identify them as an Aranet4. If the device name contains this string,
        it is considered an Aranet4 meter and it will be connected to. If
        `mac_address` is provided, this parameter is ignored.
        """
        logging.debug("Initializing Aranet4 object")
        self.loop = asyncio.get_event_loop()
        self._use_cache = use_cache
        self._magic = magic_string

        if mac_address:
            self._address = mac_address

    @property
    def mac_address(self):
        """
        The device's Bluetooth MAC address

        :return str:
        """
        return self.loop.run_until_complete(self._discover())

    @property
    def battery_level(self):
        """
        The current battery level, as a percentage (0-100)

        :return int:
        """
        return self.read_from_uuid(self.UUID_BATTERY_LEVEL)[0]

    @property
    def manufacturer_name(self):
        """
        Manufacturer name

        :return str:
        """
        return self.read_from_uuid(self.UUID_MANUFACTURER_NAME).decode("ascii")

    @property
    def model_name(self):
        """
        Model name

        :return str:
        """
        return self.read_from_uuid(self.UUID_MODEL_NAME).decode("ascii")

    @property
    def device_name(self):
        """
        Device name

        :return str:
        """
        return self.read_from_uuid(self.UUID_DEVICE_NAME).decode("ascii")

    @property
    def serial_number(self):
        """
        Serial number

        :return int:
        """
        return int(self.read_from_uuid(self.UUID_SERIAL_NUMBER))

    @property
    def hardware_revision(self):
        """
        Hardware revision number

        :return int:
        """
        return int(self.read_from_uuid(self.UUID_HARDWARE_REVISION))

    @property
    def software_revision(self):
        """
        Software revision number

        :return int:
        """
        return self.read_from_uuid(self.UUID_SOFTWARE_REVISION).decode("ascii")

    @property
    def current_readings(self):
        """
        The current settings and latest reading of all sensors of the device

        :return SimpleNamespace:
        """
        return self._get_readings(simple=False)

    @property
    def current_readings_simple(self):
        """
        The latest reading of all sensors of the device

        :return SimpleNamespace:
        """
        return self._get_readings(simple=True)

    @property
    def update_interval(self):
        """
        The pause between sensor updates

        :return int:
        """
        return le16(self.read_from_uuid(self.UUID_UPDATE_INTERVAL))

    @property
    def since_last_update(self):
        """
        The amount of seconds since the last sensor update

        :return int:
        """
        return le16(self.read_from_uuid(self.UUID_SINCE_LAST_UPDATE))

    @property
    def stored_readings_amount(self):
        """
        The amount of historical readings stored on the device

        :return int:
        """
        return le16(self.read_from_uuid(self.UUID_STORED_READINGS))

    @property
    def history(self):
        """
        The pause between sensor updates

        :return SimpleNamespace:  A namespace with an attribute for each
        sensor, and two special attributes `sensors` (all included sensors) and
        `timestamps` (a dictionary with an index -> unix timestamp map)
        """
        return self.loop.run_until_complete(self._get_history())

    def get_history(self, sensors=None, start=0x0001, end=0xFFFF):
        """
        Get historical readings stored on the device

        :param tuple sensors:  Sensors to read. More is slower. By default,
        read all four sensors. Sensors not read will be absent from the return
        value. Tuple elements should correspond to `Aranet4.SENSOR_*`
        constants.
        :param int start:  Index to start reading from (1-indexed).
        :param int end:  Index to stop reading at.
        :return SimpleNamespace:  A namespace with an attribute for each
        sensor, and two special attributes `sensors` (all included sensors) and
        `timestamps` (a dictionary with an index -> unix timestamp map)
        """
        return self.loop.run_until_complete(self._get_history(sensors, start, end))

    def read_from_uuid(self, uuid):
        """
        Read a raw value from a Bluetooth attribute by UUID

        :param str uuid:  The UUID of the attribute to read
        :return bytearray:  Value
        """
        if self._use_cache and uuid in self._cache:
            return self._cache[uuid]

        value = self.loop.run_until_complete(self._read_value(uuid))
        if self._use_cache:
            self._cache[uuid] = value

        return value

    def _normalize_value(self, value, sensor):
        """
        Normalize raw sensor value

        Some sensors may return 'magic' values or need normalization to the
        display unit. This method does that!

        :param value:  Value to normalize
        :param sensor:  What sensor the value is for
        :return:  Normalized value. `-1` if the value is not an actual sensor
        value, but e.g. a 'Calibrating' status.
        """
        if sensor == self.SENSOR_HUMIDITY:
            if (value & 0x80) == 0x80:
                return -1
        elif sensor == self.SENSOR_CO2:
            if (value & 0x8000) == 0x8000:
                return -1
        elif sensor == self.SENSOR_PRESSURE:
            if (value & 0x8000) == 0x8000:
                return -1
            else:
                return value / 10.0
        elif sensor == self.SENSOR_TEMPERATURE:
            if value == 0x4000:
                return -1
            elif value > 0x8000:
                return 0
            else:
                return value / 20.0
        else:
            raise ValueError()

        return value

    def _get_readings(self, simple=False):
        """
        Get current sensor values and settings

        :param bool simple:  Whether to only retrieve sensor values or also
        settings (slower)
        :return SimpleNamespace:
        """
        if simple:
            uuid = self.UUID_CURRENT_READING_SIMPLE
        else:
            uuid = self.UUID_CURRENT_READING_FULL

        data = self.read_from_uuid(uuid)
        values = SimpleNamespace()
        values.co2 = self._normalize_value(le16(data), self.SENSOR_CO2)
        values.temperature = self._normalize_value(le16(data, 2), self.SENSOR_TEMPERATURE)
        values.pressure = self._normalize_value(le16(data, 4), self.SENSOR_PRESSURE)
        values.humidity = self._normalize_value(data[6], self.SENSOR_HUMIDITY)
        values.battery_level = data[7]

        if not simple:
            values.update_interval = le16(data, 9)
            values.since_last_update = le16(data, 11)

        return values

    def _get_history_reader(self, sensor):
        """
        Get a callback to handle device notifications with that can access the
        Aranet4 object.

        :param int sensor:  Sensor to access
        :return:
        """
        self._datapoints = {}
        self._last_notification = time.time()

        def _receive_history(sender: int, data: bytearray):
            """
            Read chunk of archived readings

            Chunks have the following format:
            byte 1    : sensor ID (int)
            byte 2 - 3: index of first datapoint (long)
            byte 4    : number of valid datapoints in this chunk (there may be
                        more in the chunk, which can be discarded)
            byte 5+   : readings for the sensor, as a long or int depending on
                        what sensor this is

            :param int sender:  Handle of the sender Characteristic
            :param bytearray data:  Data as received
            :return:
            """
            self._last_notification = time.time()

            if data[0] != sensor:
                # notifications about a different sensor
                return

            index = le16(data, 1)
            num_points = data[3]
            data = data[4:]
            step = 1 if sensor == self.SENSOR_HUMIDITY else 2

            cursor = 0
            buffer = {}

            while len(buffer) < num_points:
                value = data[cursor:cursor + step]
                cursor += step

                value = value[0] if sensor == self.SENSOR_HUMIDITY else le16(value)

                buffer[index - 2] = self._normalize_value(value, sensor)
                index += 1

            self._datapoints = {**self._datapoints, **buffer}

        return _receive_history

    async def _get_history(self, sensors=None, start=0x0001, end=0xFFFF):
        """
        Get historical readings stored on the device

        :param tuple sensors:  Sensors to read. More is slower. By default,
        read all four sensors. Sensors not read will be absent from the return
        value.
        :param int start:  Index to start reading from (1-indexed).
        :param int end:  Index to stop reading at
        :return SimpleNamespace:  A namespace with an attribute for each
        sensor, and two special attributes `sensors` (all included sensors) and
        `timestamps` (a dictionary with an index -> unix timestamp map)
        """
        if not sensors:
            sensors = (self.SENSOR_CO2, self.SENSOR_HUMIDITY, self.SENSOR_PRESSURE, self.SENSOR_TEMPERATURE)

        if self._reading:
            raise Aranet4BusyException()

        self._reading = True
        if not self._address:
            await self._discover()

        start = start + 1
        if start < 1:
            start = 0x0001

        params = bytearray.fromhex("820000000100ffff")  # magic value?
        params = write_le16(params, 4, start)
        params = write_le16(params, 6, end)
        readings = SimpleNamespace()
        keys = ["", "temperature", "humidity", "pressure", "co2"]
        included_keys = []
        encountered_indexes = []
        index_map = {}

        interval = le16(await self._client.read_gatt_char(self.UUID_UPDATE_INTERVAL))
        for sensor in sensors:
            logging.debug("Retrieving stored values for sensor %s" % str(sensor))
            params[1] = sensor

            last_timestamp = round(time.time()) - le16(
                await self._client.read_gatt_char(self.UUID_SINCE_LAST_UPDATE))

            await self._client.write_gatt_char(self.UUID_HISTORY_RANGE, params)

            logging.debug("Asking for history")
            await self._client.start_notify(self.UUID_HISTORY_NOTIFIER, self._get_history_reader(sensor))
            while self._last_notification and time.time() - self._last_notification < 0.5:
                # 0.5 seconds seems to be sufficient, but increase if data
                # seems to be missing
                await asyncio.sleep(0.1)

            logging.debug("Received %i stored values" % len(self._datapoints))
            await self._client.stop_notify(self.UUID_HISTORY_NOTIFIER)
            self._reading = False
            encountered_indexes.append(set(self._datapoints.keys()))
            index_map[max(self._datapoints)] = last_timestamp

            # store
            readings.__setattr__(keys[sensor], self._datapoints)
            included_keys.append(keys[sensor])

        # normalize keys, in case not all sensors returned the same points
        # this can happen if the sensors update between reading different
        # sensors. In that case we discard the indexes that do not occur for
        # all sensors
        common_indexes = set.intersection(*encountered_indexes)
        for sensor in included_keys:
            sensor_data = readings.__getattribute__(sensor).copy()
            for key in sensor_data:
                if key not in common_indexes:
                    logging.debug("Discarding one uncommon datapoint from sensor %s" % str(sensor))
                    del readings.__getattribute__(sensor)[key]

        # now convert indexes to timestamps
        common_indexes = sorted(common_indexes, reverse=True)
        timestamp = index_map[common_indexes[0]]
        readings.timestamps = {}
        for index in common_indexes:
            readings.timestamps[index] = timestamp
            timestamp -= interval

        logging.debug(
            "Oldest timestamp: %s" % datetime.datetime.fromtimestamp(min(readings.timestamps.values())).strftime("%c"))
        readings.sensors = included_keys
        return readings

    async def _discover(self):
        """
        Discover Aranet4 device and initialise client

        :return str:  MAC address of the BlueTooth device
        :raises Aranet4NotFoundException:  If no device that looks like an
        Aranet4 can be found.
        """
        if not self._address:
            logging.debug("No MAC address known, starting discovery")
            devices = await BleakScanner.discover()
            for device in devices:
                if device.name is None:
                    continue
                if self._magic in device.name:
                    logging.info("Found MAC address %s for device %s" % (device.address, device.name))
                    self._address = device.address

        if not self._address:
            raise Aranet4NotFoundException("No Aranet4 device found. Try moving it closer to the Bluetooth receiver.")

        logging.info("Connecting to device %s" % self._address)
        self._client = BleakClient(self._address)
        await self._client.connect(timeout=15)
        return self._address

    async def _read_value(self, uuid):
        """
        Read GATT value from device

        :param uuid:  UUID of attribute to read from
        :return bytearray:  Returned value
        """
        await self._discover()

        try:
            value = await self._client.read_gatt_char(uuid)
        except BleakError as e:
            raise Aranet4UnpairedException("Error reading from device. Check if it is properly paired.")

        return value
