"""
Utility functions for pyaranet4
"""


def le16(data, start=0):
    """
    Read value from byte array as a long integer

    :param bytearray data:  Array of bytes to read from
    :param int start:  Offset to start reading at
    :return int:  An integer, read from the first two bytes at the offset.
    """
    raw = bytearray(data)
    return raw[start] + (raw[start + 1] << 8)


def write_le16(data, pos, value):
    """
    Write a value as a long integer to a byte array

    :param bytearray data:  Array of bytes to write to
    :param int pos:  Position to store value at as a two-byte long integer
    :param int value:  Value to store
    :return bytearray:  Updated bytearray
    """
    data[pos] = (value) & 0x00FF
    data[pos + 1] = (value >> 8) & 0x00FF

    return data
