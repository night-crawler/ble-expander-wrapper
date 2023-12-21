from dataclasses import dataclass
from typing import Optional


@dataclass
class WriteMessage:
    address: int
    buf: bytearray


@dataclass
class ReadMessage:
    address: int
    size: int
    buf: bytearray = None

    def __iter__(self):
        return iter(self.buf)


class I2cMessage:
    @staticmethod
    def write(address: int, buf: bytearray):
        return WriteMessage(address, buf)

    @staticmethod
    def read(address: int, size: int):
        return ReadMessage(address, size)


i2c_msg = I2cMessage()


class Expander:
    peripheral_address: str

    def __init__(self, peripheral_address: str):
        self.peripheral_address = peripheral_address


def pack_data_bundle(
        lock: Optional[int] = None,
        power: Optional[bool] = None,
        cs: Optional[int] = None,
        command: Optional[int] = None,
        address: Optional[int] = None,
        size_read: int = 0,
        size_write: int = 0,
        mosi: Optional[bytearray] = None,
        power_wait: int = 0,
        cs_wait: int = 0,
):
    """
    First byte is control bits:
    [lock_set, power_set, cs_set, command_set, address_set, size_read_set, size_write_set, mosi_set]
    Second byte: reserved
    [
        [0] control_bits,
        [1] reserved_control_bits,
        [2] lock_type,
        [3] power_on_off,
        [4] power_wait,
        [5] cs,
        [6] cs_wait,
        [7] command,
        [8] address,
        [9,10] [size_read, size_read],
        [11, 12] [size_write, size_write],
        [13] reserved,
        [14] reserved,
        [15] reserved,
        ..mosi
    ]
    """
    control_bits = 0
    if lock is not None:
        control_bits |= 1 << 7
    if power is not None:
        control_bits |= 1 << 6
    if cs is not None:
        control_bits |= 1 << 5
    if command is not None:
        control_bits |= 1 << 4
    if address is not None:
        control_bits |= 1 << 3
    control_bits |= 1 << 2
    control_bits |= 1 << 1
    if mosi is not None:
        control_bits |= 1 << 0

    data = bytearray(16)
    data[0] = control_bits
    if lock is not None:
        data[2] = lock

    if power is not None:
        data[3] = 1 if power else 0
    data[4] = power_wait

    if cs is not None:
        data[5] = cs
    data[6] = cs_wait

    if command is not None:
        data[7] = command
    if address is not None:
        data[8] = address
    if size_read is not None:
        data[9] = size_read & 0xFF
        data[10] = (size_read >> 8) & 0xFF
    if size_write is not None:
        data[11] = size_write & 0xFF
        data[12] = (size_write >> 8) & 0xFF
    if mosi is not None:
        data[16:] = mosi

    return data


def compute_r(c, m, d, b):
    if m < -10 or m > 10:
        raise ValueError("Multiplier should be between -10 and +10")
    return c * m * (10 ** d) * (2 ** b)


def deserialize_temperature(data: bytearray):
    value = int.from_bytes(data, byteorder='little', signed=True)
    value = compute_r(value, 1, -2, 0)

    return value


def deserialize_pressure(data: bytearray):
    #  M = 1, d = -1, b = 0
    value = int.from_bytes(data, byteorder='little', signed=True)
    value = compute_r(value, 1, -1, 0)

    return value


def deserialize_humidity(data: bytearray):
    # M = 1, d = -2, b = 0
    value = int.from_bytes(data, byteorder='little', signed=True)
    value = compute_r(value, 1, -2, 0)

    return value


def deserialize_float(data: bytearray):
    import struct
    value = struct.unpack('f', data)
    return value[0]
