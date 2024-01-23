import enum

from ble_collector_client import BleCollectorClient
import typing_extensions

from dto import IoCommand, Fqcn, PeripheralIoBatchRequestDto, PeripheralIoRequestDto

if typing_extensions.TYPE_CHECKING:
    from ble_collector_client import BleCollectorClient


class Command(enum.Enum):
    PRESS = b'\x57\x01\x00'
    ON = b'\x57\x01\x01'
    OFF = b'\x57\x01\x02'
    OPEN = b'\x57\x0F\x45\x01\x05\xFF\x00'
    CLOSE = b'\x57\x0F\x45\x01\x05\xFF\x64'
    PAUSE = b'\x57\x0F\x45\x01\x00\xFF'


class SwitchBotService:
    service_uuid = 'cba20d00-224d-11e6-9fb8-0002a5d5c51b'
    char_uuid = 'cba20002-224d-11e6-9fb8-0002a5d5c51b'

    timeout_ms: int = 50000

    def __init__(self, client: 'BleCollectorClient', adapter_id: str, peripheral: str):
        self.client = client
        self.adapter_id = adapter_id
        self.peripheral = peripheral

    def _build_command(self, cmd: Command):
        return IoCommand.write(
            fqcn=Fqcn(
                peripheral=self.peripheral,
                service=self.service_uuid,
                characteristic=self.char_uuid
            ),
            value=[*cmd.value],
            wait_response=False,
            timeout_ms=self.timeout_ms
        )

    def send_request(self):
        request = PeripheralIoRequestDto(
            batches=[
                PeripheralIoBatchRequestDto(
                    commands=[self._build_command(Command.PRESS)],
                    parallelism=1
                )
            ],
            parallelism=1
        )

        response = self.client.write_read_peripheral_value(self.adapter_id, request)

        return response
