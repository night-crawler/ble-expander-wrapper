from loguru import logger

from bme_calibrator_service import Bme280CalibratorService
from contrib.scd import SCD4X
from expander import Expander
from ble_timeout_setter_service import BleTimeoutSetter
from metrics import *


def read_scd41(client, adapter, peripheral_address):
    expander_service = Expander(client, adapter, peripheral_address, timeout_ms=10000)

    try:
        scd = SCD4X(expander_service, quiet=False)
        scd.start_periodic_measurement()
        co2, temperature, relative_humidity, _ = scd.measure(timeout=15)

        CO2.labels(peripheral=peripheral_address, scope='scd41').set(co2)
        TEMPERATURE.labels(peripheral=peripheral_address, scope='scd41').set(temperature)
        HUMIDITY.labels(peripheral=peripheral_address, scope='scd41').set(relative_humidity)

        logger.info(f'CO2: {co2} ppm, Temperature: {temperature} C, Humidity: {relative_humidity} %rH')

    except Exception as e:
        logger.error(f'Failed to read Expander: {e}', exc_info=True)
    finally:
        try:
            expander_service.set_lock(0)
        except Exception as e:
            logger.error(f'Failed to release Expander lock: {e}', exc_info=True)


def calibrate(client, adapter, peripherals):
    service = Bme280CalibratorService(client, adapter)
    result = service.calibrate_humidity_offset(
        peripherals,
        72.0, 102.4 * 1000, 21.9
    )
    logger.info(f'Calibration result: {result}')


def set_timeout(client, adapter, peripheral_address, timeout_ms):
    try:
        service = BleTimeoutSetter(client, adapter)
        result = service.set_all_timeouts(peripheral_address, timeout_ms)
        logger.info(f'Set timeout result: {result}')
    except Exception as e:
        logger.error(f'Failed to set timeout: {e}')
