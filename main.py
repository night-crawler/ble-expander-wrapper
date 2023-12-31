import os
from time import sleep

from prometheus_client import start_http_server

from ble_collector_client import BleCollectorClient
from routines import set_timeout, read_scd41

PERIPHERALS = [
    'D0:F6:3B:34:4C:1F',
    'D4:B7:67:56:DC:3B',
    'FA:6F:EC:EE:4B:36',
]

if __name__ == '__main__':
    start_http_server(12500)
    collector_address = os.environ.get('COLLECTOR_ADDRESS', 'http://127.0.0.1:9090')
    adapter_id = os.environ.get('ADAPTER', 'hci0')

    client = BleCollectorClient(address=collector_address)
    set_timeout(client, adapter_id, PERIPHERALS, 60000)

    counter = 0
    while True:
        if counter % 5 == 0:
            set_timeout(client, adapter_id, PERIPHERALS, 60000)

        read_scd41(client, adapter_id, 'FA:6F:EC:EE:4B:36')
        sleep(60)

        counter += 1
