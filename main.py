from ble_collector_client import BleCollectorClient
from contrib.scd import SCD4X
from dto import *
from expander import Expander

DATA_BUNDLE_UUID = "0000a001-0000-1000-8000-00805f9b34fb"
MISO_UUID = "0000a002-0000-1000-8000-00805f9b34fb"
CS_UUID = "0000a003-0000-1000-8000-00805f9b34fb"
LOCK_UUID = "0000a004-0000-1000-8000-00805f9b34fb"
POWER_UUID = "0000a005-0000-1000-8000-00805f9b34fb"
RESULT_UUID = "0000a006-0000-1000-8000-00805f9b34fb"

if __name__ == '__main__':
    client = BleCollectorClient()
    expander_service = Expander(client, 'hci0', 'FA:6F:EC:EE:4B:36')

    scd = SCD4X(expander_service, quiet=False)
    scd.start_periodic_measurement()
    co2, temperature, relative_humidity, _ = scd.measure(timeout=15)

    print(f'CO2: {co2} ppm, Temperature: {temperature} C, Humidity: {relative_humidity} %rH')

    #
    # print(client.list_adapters())
    # print(client.describe_adapters())
    # b = [q for q in (2).to_bytes(1, 'little', signed=False)]
    # r = PeripheralIoRequestDto(
    #     batches=[
    #         PeripheralIoBatchRequestDto(
    #             commands=[
    #                 IoCommand.write(
    #                     fqcn=Fqcn(
    #                         peripheral_address='FA:6F:EC:EE:4B:36',
    #                         service_uuid='ac866789-aaaa-eeee-a329-969d4bc8621e',
    #                         characteristic_uuid=LOCK_UUID
    #                     ),
    #                     value=b,
    #                     wait_response=True
    #                 ),
    #
    #                 IoCommand.read(
    #                     fqcn=Fqcn(
    #                         peripheral_address='FA:6F:EC:EE:4B:11',
    #                         service_uuid='ac866789-aaaa-eeee-a329-969d4bc8621e',
    #                         characteristic_uuid=RESULT_UUID,
    #                     ),
    #                     wait_notification=True,
    #                     timeout_ms=2000,
    #                 ),
    #
    #             ],
    #             parallelism=32
    #         )
    #
    #     ],
    #     parallelism=4
    # )
    # print(client.write_read_peripheral_value('hci0', r))
