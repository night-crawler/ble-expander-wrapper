import requests

from dto import *
from error import ApiException


class BleCollectorClient:
    address: str

    def __init__(self, address: str = 'http://127.0.0.1:8000') -> None:
        self.address = address

    def list_adapters(self) -> list[AdapterInfoDto]:
        result = requests.get(f'{self.address}/ble/adapters')
        if result.status_code != 200:
            raise ApiException(result.status_code, text=result.text)
        json = result.json()['data']

        return [*map(AdapterInfoDto.from_dict, json)]

    def describe_adapters(self):
        result = requests.get(f'{self.address}/ble/adapters/describe')
        if result.status_code != 200:
            raise ApiException(result.status_code, text=result.text)

        json = result.json()['data']
        return [*map(AdapterDto.from_dict, json)]

    def write_read_peripheral_value(
            self,
            adapter_id: str,
            io_request: PeripheralIoRequestDto
    ) -> PeripheralIoResponseDto:
        data = io_request.to_dict()
        drop_nulls(data)
        result = requests.post(f'{self.address}/ble/adapters/{adapter_id}/io', json=data)
        if result.status_code != 200:
            raise ApiException(result.status_code, text=result.text)
        json = result.json()['data']
        return PeripheralIoResponseDto.from_dict(json)


def drop_nulls(data):
    if data is None:
        return
    if isinstance(data, dict):
        none_keys = [k for k, v in data.items() if v is None]
        for key in none_keys:
            del data[key]
        for v in data.values():
            drop_nulls(v)
    if isinstance(data, list):
        for v in data:
            drop_nulls(v)
