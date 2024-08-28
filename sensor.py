from datetime import timedelta
import logging

from bleak import BleakScanner

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)  # Adjust as necessary


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the SeeLevel BLE volume storage sensor."""
    service_uuid = config.get("service_uuid")
    if not service_uuid:
        _LOGGER.error("No Service UUID provided")
        return

    sensor = SeeLevelBLEVolumeStorageSensor(service_uuid)
    async_add_entities([sensor])

    async_track_time_interval(hass, sensor.async_update, SCAN_INTERVAL)


class SeeLevelBLEVolumeStorageSensor(SensorEntity):
    def __init__(self, service_uuid):
        """Initialize the sensor."""
        _LOGGER.info("Initializing SeeLevel BLE Volume Storage Sensor")
        self.service_uuid = service_uuid
        self._state = None
        self._name = f"SeeLevel BLE Service UUID {service_uuid}"
        self._attributes = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "gal"

    async def async_update(self, *args):
        """Fetch new state data for the sensor."""
        scanner = BleakScanner()
        devices = await scanner.discover()
        _LOGGER.info(f"Found {len(devices)} BLE devices")
        for device in devices:
            _LOGGER.info(f"Device: {device}")
            for adv_data in device.metadata.get("uuids", []):
                if self._service_uuid.lower() == adv_data.lower():
                    _LOGGER.info(
                        f"Found BLE device with Service UUID {self._service_uuid}"
                    )
                    self._state = self.parse_advertisement(device)
                    return

    def parse_advertisement(self, device):
        """Parse the BLE advertisement data to extract the volume storage and other sensor details."""
        manufacturer_data = device.metadata.get("manufacturer_data", {})
        sensor_data = manufacturer_data.get(
            0xFFFF
        )  # Replace with your specific manufacturer ID

        if sensor_data:
            sensor_type_byte = sensor_data[3]
            sensor_type = self.get_sensor_type(sensor_type_byte)

            sensor_data_ascii = sensor_data[4:7].decode("ascii")
            sensor_volume = int.from_bytes(sensor_data[7:10], byteorder="little")
            sensor_total = int.from_bytes(sensor_data[10:13], byteorder="little")

            _LOGGER.info(f"Sensor Type: {sensor_type}")
            _LOGGER.info(f"Sensor Data (ASCII): {sensor_data_ascii}")
            _LOGGER.info(f"Sensor Volume: {sensor_volume} gallons")
            _LOGGER.info(f"Sensor Total: {sensor_total} gallons")

            # Set extra attributes for the sensor
            self._attributes = {
                "sensor_type": sensor_type,
                "sensor_data_ascii": sensor_data_ascii,
                "sensor_total": sensor_total,
            }

            # Here you can choose what to return as the state. For example:
            return (
                sensor_volume  # Or return some other value depending on your use case
            )

        return None


def get_sensor_type(self, byte_value):
    """Return a string representing the sensor type based on the byte value."""
    sensor_types = {
        0: "Fresh",
        1: "Black",
        2: "Gray",
        3: "LPG",
        4: "LPG2",
        5: "Galley",
        6: "Galley 2",
    }
    return sensor_types.get(byte_value, "Unknown")
