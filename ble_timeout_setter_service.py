import enum

import typing_extensions

from dto import IoCommand, Fqcn, PeripheralIoBatchRequestDto, PeripheralIoRequestDto

if typing_extensions.TYPE_CHECKING:
    from ble_collector_client import BleCollectorClient


class ServiceType(enum.Enum):
    DEVICE_INFORMATION = 'device_information'
    BME280 = 'bme280'
    LIS2DH12 = 'lis2dh12'
    ADC = 'adc'
    VEML6040 = 'veml6040'


TIMEOUT_MAP = {
    ServiceType.DEVICE_INFORMATION: (
        '0000180a-0000-1000-8000-00805f9b34fb', 'a0e4d2ba-0002-8000-8789-00805f9b34fb'
    ),
    ServiceType.BME280: (
        '5c853275-723b-4754-a329-969d4bc8121e', 'a0e4a2ba-0000-8000-0000-00805f9b34fb'
    ),
    ServiceType.LIS2DH12: (
        '5c853275-823b-4754-a329-969d4bc8121e', 'a0e4a2ba-0000-8000-0000-00805f9b34fb'
    ),
    ServiceType.ADC: (
        '5c853275-723b-4754-a329-969d8bc8121d', 'a0e4d2ba-0002-8000-0000-00805f9b34fb'
    ),
    ServiceType.VEML6040: (
        '5c853275-923b-4754-a329-969d4bc8121e', 'a0e4a2ba-0000-8000-0000-00805f9b34fb'
    )
}


class BleTimeoutSetter:
    timeout_ms: int = 5000

    def __init__(self, client: 'BleCollectorClient', adapter_id: str, timeout_ms: int = 5000):
        self.client = client
        self.adapter_id = adapter_id
        self.timeout_ms = timeout_ms

    def build_set_timeout_cmd(self, peripheral: str, service: str, characteristic: str, notification_timeout: int):
        return IoCommand.write(
            fqcn=Fqcn(
                peripheral_address=peripheral,
                service_uuid=service,
                characteristic_uuid=characteristic
            ),
            value=[*notification_timeout.to_bytes(4, 'little', signed=False)],
            wait_response=True,
            timeout_ms=self.timeout_ms
        )

    def build_notification_timeout_batch(self, peripheral: str, timeout_map: dict[ServiceType, int]):
        commands = []
        for service_type, notification_timeout in timeout_map.items():
            service_uuid, characteristic_uuid = TIMEOUT_MAP[service_type]
            commands.append(
                self.build_set_timeout_cmd(
                    peripheral,
                    service_uuid,
                    characteristic_uuid,
                    notification_timeout)
            )

        return PeripheralIoBatchRequestDto(commands=commands, parallelism=10)

    def set_all_timeouts(self, peripherals: list[str], notification_timeout_ms: int):
        timeout_map = dict.fromkeys(ServiceType, notification_timeout_ms)

        batches = [
            self.build_notification_timeout_batch(peripheral, timeout_map)
            for peripheral in peripherals
        ]

        request = PeripheralIoRequestDto(batches=batches, parallelism=min(10, len(peripherals)))
        return self.client.write_read_peripheral_value(self.adapter_id, request)
