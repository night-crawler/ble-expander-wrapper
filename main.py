from ble_collector_client import BleCollectorClient
from contrib.scd import SCD4X
from expander import Expander
from ble_timeout_setter_service import BleTimeoutSetter

DATA_BUNDLE_UUID = "0000a001-0000-1000-8000-00805f9b34fb"
MISO_UUID = "0000a002-0000-1000-8000-00805f9b34fb"
CS_UUID = "0000a003-0000-1000-8000-00805f9b34fb"
LOCK_UUID = "0000a004-0000-1000-8000-00805f9b34fb"
POWER_UUID = "0000a005-0000-1000-8000-00805f9b34fb"
RESULT_UUID = "0000a006-0000-1000-8000-00805f9b34fb"

peripherals = [
    'D0:F6:3B:34:4C:1F',
    'D4:B7:67:56:DC:3B',
    'FA:6F:EC:EE:4B:36',
]

if __name__ == '__main__':
    client = BleCollectorClient(address='http://192.168.0.220:9090')
    # client = BleCollectorClient()
    expander_service = Expander(client, 'hci0', 'FA:6F:EC:EE:4B:36', timeout_ms=10000)
    timeout_setter = BleTimeoutSetter(client, 'hci0')

    print(timeout_setter.set_all_timeouts(peripherals, 10000))

    # expander_service.set_lock(2)
    # expander_service.set_power(False)
    #

    try:
        scd = SCD4X(expander_service, quiet=False)
        scd.start_periodic_measurement()
        co2, temperature, relative_humidity, _ = scd.measure(timeout=15)
    finally:
        expander_service.set_lock(0)
        # expander_service.set_power(False)
        pass

    print(f'CO2: {co2} ppm, Temperature: {temperature} C, Humidity: {relative_humidity} %rH')

    # q = expander_service.calibrate_humidity_offset(
    #     [
    #         'D0:F6:3B:34:4C:1F',
    #         'D4:B7:67:56:DC:3B',
    #         'FA:6F:EC:EE:4B:36',
    #     ],
    #     72.0, 102.4 * 1000, 21.9
    # )
