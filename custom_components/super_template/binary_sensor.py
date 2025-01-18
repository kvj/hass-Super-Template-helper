
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import binary_sensor

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("binary_sensor", _Entity))
    return True

class _Entity(BaseEntity, binary_sensor.BinarySensorEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def device_class(self):
        if value := self.coordinator.data.get("device_class"):
            return binary_sensor.BinarySensorDeviceClass(value)

    @property
    def is_on(self):
        return self.coordinator.data.get("value")
