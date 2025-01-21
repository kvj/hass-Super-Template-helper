
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import number

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("number", _Entity))
    return True

class _Entity(BaseEntity, number.NumberEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def device_class(self):
        return self.data_as_enum("device_class", number.NumberDeviceClass)

    @property
    def mode(self):
        return self.data("mode")

    @property
    def native_max_value(self):
        return self.data("max_value")

    @property
    def native_min_value(self):
        return self.data("min_value")

    @property
    def native_step(self):
        return self.data("step")

    @property
    def native_value(self):
        return self.data("value")

    @property
    def native_unit_of_measurement(self):
        return self.data("unit_of_measurement")

    async def async_set_native_value(self, value: float):
        return await self.coordinator.async_execute_action("on_set", {"value": value})
