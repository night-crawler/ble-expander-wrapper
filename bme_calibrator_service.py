import struct

import typing_extensions
from loguru import logger

from dto import IoCommand, Fqcn, PeripheralIoBatchRequestDto, PeripheralIoRequestDto
from util import deserialize_humidity, deserialize_pressure, \
    deserialize_temperature, deserialize_float

if typing_extensions.TYPE_CHECKING:
    from ble_collector_client import BleCollectorClient

BME280_SERVICE = '5c853275-723b-4754-a329-969d4bc8121e'
HUMIDITY_CALIBRATION_CH = 'a0e4a2ba-1234-4321-0001-00805f9b34fb'
TEMPERATURE_CALIBRATION_CH = 'a0e4a2ba-1234-4321-0002-00805f9b34fb'
PRESSURE_CALIBRATION_CH = 'a0e4a2ba-1234-4321-0003-00805f9b34fb'

TEMPERATURE_CH = '00002a6e-0000-1000-8000-00805f9b34fb'
PRESSURE_CH = '00002a6d-0000-1000-8000-00805f9b34fb'
HUMIDITY_CH = '00002a6f-0000-1000-8000-00805f9b34fb'


class Ble280Calibrator:
    timeout_ms: int = 5000

    def __init__(self, client: 'BleCollectorClient', adapter_id: str, timeout_ms: int = 5000):
        self.client = client
        self.adapter_id = adapter_id
        self.timeout_ms = timeout_ms

    def calibrate_humidity_offset(
            self, peripherals: list[str],
            target_humidity: float, target_pressure: float, target_temperature: float):
        def create_read_batch(characteristic):
            return PeripheralIoBatchRequestDto(commands=[
                IoCommand.read(
                    fqcn=Fqcn(
                        peripheral_address=peripheral,
                        service_uuid=BME280_SERVICE,
                        characteristic_uuid=characteristic
                    ),
                    wait_notification=False,
                    timeout_ms=self.timeout_ms,
                )
                for peripheral in peripherals
            ], parallelism=32)

        request = PeripheralIoRequestDto(batches=[
            create_read_batch(HUMIDITY_CH),
            create_read_batch(TEMPERATURE_CH),
            create_read_batch(PRESSURE_CH),

            create_read_batch(HUMIDITY_CALIBRATION_CH),
            create_read_batch(TEMPERATURE_CALIBRATION_CH),
            create_read_batch(PRESSURE_CALIBRATION_CH),
        ], parallelism=4)

        write_commands = []

        def add_write_command(peripheral, ch, value):
            write_commands.append(
                IoCommand.write(
                    fqcn=Fqcn(
                        peripheral_address=peripheral,
                        service_uuid=BME280_SERVICE,
                        characteristic_uuid=ch
                    ),
                    value=[*value],
                    wait_response=True,
                    timeout_ms=self.timeout_ms
                )
            )

        responses = [
            responses.command_responses
            for responses in
            self.client.write_read_peripheral_value(self.adapter_id, request).batch_responses
        ]
        for (peripheral, ah, at, ap, ch, ct, cp) in zip(peripherals, *responses):
            current_h = deserialize_humidity(ah.Ok)
            current_t = deserialize_temperature(at.Ok)
            current_p = deserialize_pressure(ap.Ok)

            current_offset_h = deserialize_float(bytearray(ch.Ok))
            current_offset_t = deserialize_float(bytearray(ct.Ok))
            current_offset_p = deserialize_float(bytearray(cp.Ok))

            actual_h = current_h - current_offset_h
            actual_t = current_t - current_offset_t
            actual_p = current_p - current_offset_p

            next_offset_h = target_humidity - actual_h
            next_offset_t = target_temperature - actual_t
            next_offset_p = target_pressure - actual_p

            logger.info(f'[{peripheral}] Current Humidity: {current_h} = {actual_h} + {current_offset_h}; '
                        f'next offset: {next_offset_h}')
            logger.info(f'Current Temperature: {current_t} = {actual_t} + {current_offset_t}; '
                        f'next offset: {next_offset_t}')
            logger.info(f'Current Pressure: {current_p} = {actual_p} + {current_offset_p}; '
                        f'next offset: {next_offset_p}')

            # next_offset_h = 0.0
            # next_offset_t = 0.0
            # next_offset_p = 0.0

            next_offset_h = struct.pack('<f', next_offset_h)
            next_offset_t = struct.pack('<f', next_offset_t)
            next_offset_p = struct.pack('<f', next_offset_p)

            add_write_command(peripheral, HUMIDITY_CALIBRATION_CH, next_offset_h)
            add_write_command(peripheral, TEMPERATURE_CALIBRATION_CH, next_offset_t)
            add_write_command(peripheral, PRESSURE_CALIBRATION_CH, next_offset_p)

        batch_request = PeripheralIoBatchRequestDto(commands=write_commands, parallelism=32)
        request = PeripheralIoRequestDto(batches=[batch_request], parallelism=4)

        return self.client.write_read_peripheral_value(self.adapter_id, request)
