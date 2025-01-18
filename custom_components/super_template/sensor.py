
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import sensor

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("sensor", _Entity))
    return True

class _Entity(BaseEntity, sensor.SensorEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def device_class(self):
        if value := self.coordinator.data.get("device_class"):
            return sensor.const.SensorDeviceClass(value)
    
    @property
    def state_class(self):
        return self.coordinator.data.get("state_class")
    
    @property
    def suggested_display_precision(self):
        return self.coordinator.data.get("display_precision")
    
    @property
    def native_unit_of_measurement(self):
        return self.coordinator.data.get("unit_of_measurement")

    @property
    def native_value(self):
        return self.coordinator.data.get("value")
    