
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import valve

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("valve", _Entity))
    return True

class _Entity(BaseEntity, valve.ValveEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def device_class(self):
        return self.data_as_enum("device_class", valve.ValveDeviceClass)

    @property
    def current_valve_position(self):
        return self.data("value")

    @property
    def is_closed(self):
        return self.data("is_closed")

    @property
    def is_closing(self):
        return self.data("is_closing")

    @property
    def is_opening(self):
        return self.data("is_opening")

    @property
    def reports_position(self):
        return self.data("reports_position", False)

    @property
    def supported_features(self):
        return self.data_as_or("supported_features", valve.ValveEntityFeature)
    
    async def async_open_valve(self) -> None:
        return await self.coordinator.async_execute_action("on_open", {})

    async def async_close_valve(self) -> None:
        return await self.coordinator.async_execute_action("on_close", {})

    async def async_set_valve_position(self, position: int) -> None:
        return await self.coordinator.async_execute_action("on_position", {"position": position})

    async def async_stop_valve(self) -> None:
        return await self.coordinator.async_execute_action("on_stop", {})
