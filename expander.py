import typing_extensions
from loguru import logger

from dto import IoCommand, Fqcn, PeripheralIoBatchRequestDto, PeripheralIoRequestDto, PeripheralIoBatchResponseDto, \
    CommandResponse
from util import pack_data_bundle, WriteMessage, ReadMessage

if typing_extensions.TYPE_CHECKING:
    from ble_collector_client import BleCollectorClient

DATA_BUNDLE_UUID = "0000a001-0000-1000-8000-00805f9b34fb"
MISO_UUID = "0000a002-0000-1000-8000-00805f9b34fb"
CS_UUID = "0000a003-0000-1000-8000-00805f9b34fb"
LOCK_UUID = "0000a004-0000-1000-8000-00805f9b34fb"
POWER_UUID = "0000a005-0000-1000-8000-00805f9b34fb"
RESULT_UUID = "0000a006-0000-1000-8000-00805f9b34fb"

ID_MAP = {
    DATA_BUNDLE_UUID: 1,
    CS_UUID: 2,
    LOCK_UUID: 3,
    POWER_UUID: 4,
    RESULT_UUID: 5,
}

ID_NAME_MAP = {
    1: 'DATA_BUNDLE',
    2: 'CS',
    3: 'COMMAND',
    4: 'LOCK',
    6: 'POWER',
    7: 'SIZE',
    8: 'ADDRESS',
}


class ExpanderError(Exception):
    @classmethod
    def from_command_id(cls, command_id: int):
        command_name = ID_NAME_MAP.get(command_id, 'UNKNOWN')
        return cls(f'Command {command_name} failed')


class Expander:
    SERVICE_UUID = 'ac866789-aaaa-eeee-a329-969d4bc8621e'
    power_wait: int = 1
    timeout_ms: int = 5000

    def __init__(self, client: 'BleCollectorClient', adapter_id: str, peripheral_address: str, timeout_ms: int = 5000):
        self.client = client
        self.peripheral_address = peripheral_address
        self.adapter_id = adapter_id
        self.timeout_ms = timeout_ms

    @staticmethod
    def _build_batch(*commands, parallelism: int = 32):
        return PeripheralIoBatchRequestDto(
            commands=commands,
            parallelism=parallelism
        )

    def _build_write(self, characteristic_uuid: str, value, wait_response: bool = False, timeout_ms: int = 2000):
        return IoCommand.write(
            fqcn=Fqcn(
                peripheral_address=self.peripheral_address,
                service_uuid=self.SERVICE_UUID,
                characteristic_uuid=characteristic_uuid
            ),
            value=value,
            wait_response=wait_response,
            timeout_ms=timeout_ms,
        )

    def _build_read(self, characteristic_uuid: str, wait_notification: bool = True, timeout_ms: int = 2000):
        return IoCommand.read(
            fqcn=Fqcn(
                peripheral_address=self.peripheral_address,
                service_uuid=self.SERVICE_UUID,
                characteristic_uuid=characteristic_uuid,
            ),
            wait_notification=wait_notification,
            timeout_ms=timeout_ms,
        )

    @staticmethod
    def _build_request(*batches, parallelism: int = 4):
        return PeripheralIoRequestDto(
            batches=batches,
            parallelism=parallelism
        )

    def _client_read(self, characteristic_uuid: str):
        request = self._build_request(
            self._build_batch(
                self._build_read(characteristic_uuid, wait_notification=False, timeout_ms=self.timeout_ms),
                parallelism=1
            ),
            parallelism=1
        )
        response = self.client.write_read_peripheral_value(self.adapter_id, request)
        batch = response.batch_responses[0]
        self._validate_batch(batch)
        return batch.command_responses[0].Ok

    def _client_write_read(self, write_characteristic_uuid: str, value):
        request = self._build_request(
            self._build_batch(
                self._build_write(write_characteristic_uuid, [*value], wait_response=False, timeout_ms=self.timeout_ms),
                self._build_read(RESULT_UUID, timeout_ms=self.timeout_ms)
            ),
            parallelism=16
        )
        response = self.client.write_read_peripheral_value(self.adapter_id, request)
        batch = response.batch_responses[0]
        self._validate_batch(batch)
        command_id = self._interpret_response(batch.command_responses[1])

        logger.info(f"Command {command_id} returned {batch.command_responses[1].Ok}")

        return batch

    @staticmethod
    def _validate_batch(batch: PeripheralIoBatchResponseDto):
        for response in batch.command_responses:
            if response is None:
                continue
            if response.Error is not None:
                raise ExpanderError(response.Error)

    @staticmethod
    def _interpret_response(command_response: CommandResponse):
        value = command_response.Ok
        result_code = int.from_bytes(value, byteorder='little', signed=True)
        if result_code < -100:
            command_id = result_code + 128
        elif result_code < 0:
            command_id = -result_code
        else:
            command_id = result_code

        is_success = result_code >= 0
        if not is_success:
            raise ExpanderError.from_command_id(command_id)

        return command_id

    def set_bundle(self, data: bytearray):
        self._client_write_read(DATA_BUNDLE_UUID, data)

    def read_miso(self):
        return self._client_read(MISO_UUID)

    def set_cs(self, cs: int):
        self._client_write_read(CS_UUID, cs.to_bytes(1, 'little', signed=False))

    def set_lock(self, lock_type: int):
        self._client_write_read(LOCK_UUID, lock_type.to_bytes(1, 'little', signed=False))

    def set_power(self, on: bool):
        self._client_write_read(POWER_UUID, on.to_bytes(1, 'little', signed=False))

    def xfer(self, buf: bytearray, *args, **kwargs):
        """
        0x00 => Ok(Command::Write),
        0x01 => Ok(Command::Read),
        0x02 => Ok(Command::Transfer),
        """

        bundle = pack_data_bundle(
            lock=1, power=True, command=2, size_write=len(buf), mosi=buf,
            power_wait=self.power_wait
        )
        self.set_bundle(bundle)
        return self.read_miso()

    def scan_i2c(self):
        bundle = pack_data_bundle(
            lock=2, power=True, command=3, address=0, size_write=0, mosi=bytearray(),
            power_wait=self.power_wait
        )
        self.set_bundle(bundle)
        return [address for address in self.read_miso() if address != 0]

    def write(self, address: int, buf: bytearray):
        bundle = pack_data_bundle(
            lock=2, power=True, command=0, address=address, size_write=len(buf), mosi=buf,
            power_wait=self.power_wait
        )
        return self.set_bundle(bundle)

    def read(self, address: int, size: int):
        bundle = pack_data_bundle(
            lock=2, power=True, command=1, address=address, size_read=size
        )
        self.set_bundle(bundle)
        result = self.read_miso()
        return result[:size]

    def write_read(self, address: int, buf: bytearray, size_read: int):
        bundle = pack_data_bundle(
            lock=2, power=True, command=2, address=address, size_write=len(buf), size_read=size_read, mosi=buf)
        self.set_bundle(bundle)
        return self.read_miso()[:size_read]

    def i2c_rdwr(self, *messages):
        for message in messages:
            match message:
                case WriteMessage(address, buf):
                    self.write(address, buf)
                    logger.info("Wrote {} bytes to address {}", len(buf), address)
                case ReadMessage(address=address, size=size):
                    result = self.read(address, size)
                    message.buf = result
                    logger.info("Read {} bytes from address {}: {}", size, address, result)


