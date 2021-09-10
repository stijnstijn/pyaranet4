class Aranet4Exception(BaseException):
    """
    Base exception for pyaranet4
    """
    pass


class Aranet4NotFoundException(Aranet4Exception):
    """
    Exception that occurs when no suitable Aranet4 device is available
    """
    pass


class Aranet4BusyException(Aranet4Exception):
    """
    Exception that occurs when one attempts to fetch history from the device
    while history for another sensor is being read
    """
    pass


class Aranet4UnpairedException(Aranet4Exception):
    """
    Exception that occurs when the Aranet4 device is detected but unpaired, and
    no data can be read from it.
    """
    pass
