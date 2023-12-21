from prometheus_client import Gauge

CO2 = Gauge('sensor_hub_scd41_co2_ppm', 'CO2', ['peripheral', 'scope'])
HUMIDITY = Gauge('sensor_hub_scd41_humidity_percent', 'Humidity', ['peripheral', 'scope'])
TEMPERATURE = Gauge('sensor_hub_scd41_temperature_degrees_celsius', 'Temperature', ['peripheral', 'scope'])
