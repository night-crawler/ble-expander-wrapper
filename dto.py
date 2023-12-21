import enum
from dataclasses import dataclass
from typing import Any, Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class AdapterInfoDto:
    id: str
    modalias: str


@dataclass_json
@dataclass
class Fqcn:
    peripheral_address: str
    service_uuid: str
    characteristic_uuid: str


@dataclass_json
@dataclass
class IoWriteCommand:
    fqcn: Fqcn
    value: list[int]
    wait_response: bool
    timeout_ms: int


@dataclass_json
@dataclass
class IoReadCommand:
    fqcn: Fqcn
    wait_notification: bool
    timeout_ms: int


@dataclass_json
@dataclass
class IoCommand:
    Write: Optional[IoWriteCommand] = None
    Read: Optional[IoReadCommand] = None

    @classmethod
    def write(cls, fqcn: Fqcn, value: list, wait_response: bool, timeout_ms: int):
        return IoCommand(Write=IoWriteCommand(fqcn=fqcn, value=value, wait_response=wait_response, timeout_ms=timeout_ms))

    @classmethod
    def read(cls, fqcn: Fqcn, wait_notification: bool, timeout_ms: int):
        return IoCommand(Read=IoReadCommand(fqcn=fqcn, wait_notification=wait_notification, timeout_ms=timeout_ms))


@dataclass_json
@dataclass
class PeripheralIoBatchRequestDto:
    commands: list[IoCommand]
    parallelism: int


@dataclass_json
@dataclass
class PeripheralIoRequestDto:
    batches: list[PeripheralIoBatchRequestDto]
    parallelism: int


@dataclass_json
@dataclass
class CommandResponse:
    Ok: Optional[Any] = None
    Error: Optional[Any] = None


@dataclass_json
@dataclass
class PeripheralIoBatchResponseDto:
    command_responses: list[Optional[CommandResponse]]


@dataclass_json
@dataclass
class PeripheralIoResponseDto:
    batch_responses: list[PeripheralIoBatchResponseDto]


class CharPropDto(enum.Enum):
    Broadcast = 'Broadcast'
    Read = 'Read'
    WriteWithoutResponse = 'WriteWithoutResponse'
    Write = 'Write'
    Notify = 'Notify'
    Indicate = 'Indicate'
    AuthenticatedSignedWrites = 'AuthenticatedSignedWrites'
    ExtendedProperties = 'ExtendedProperties'
    Unknown = 'Unknown'


@dataclass_json
@dataclass
class Descriptor:
    uuid: str
    service_uuid: str
    characteristic_uuid: str


@dataclass_json
@dataclass
class Characteristic:
    uuid: str
    service_uuid: str
    properties: list[CharPropDto]
    descriptors: list[Descriptor]


@dataclass_json
@dataclass
class Service:
    uuid: str
    primary: bool
    characteristics: list[Characteristic]


class AddressType(enum.Enum):
    Public = 'Public'
    Random = 'Random'


@dataclass_json
@dataclass
class Prop:
    address: str
    address_type: AddressType
    manufacturer_data: Optional[Any]
    service_data: Optional[Any]
    services: list[str]
    local_name: Optional[str] = None
    tx_power_level: Optional[int] = None
    rssi: Optional[int] = None
    class_: Optional[int] = None


@dataclass_json
@dataclass
class Peripheral:
    id: str
    address: str
    props: Optional[Prop]
    services: list['Service']


@dataclass_json
@dataclass
class AdapterDto:
    adapter_info: AdapterInfoDto
    peripherals: list['Peripheral']


