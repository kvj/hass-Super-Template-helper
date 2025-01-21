
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import device_tracker

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("device_tracker", _Entity))
    return True

class _Entity(BaseEntity, device_tracker.config_entry.TrackerEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def battery_level(self):
        return self.data("battery_level")

    @property
    def latitude(self):
        return self.data("latitude")

    @property
    def longitude(self):
        return self.data("longitude")
    
    @property
    def location_accuracy(self):
        return self.data("accuracy")

    @property
    def location_name(self):
        return self.data("value")

    @property
    def source_type(self):
        return self.data_as_enum("source_type", device_tracker.const.SourceType)
