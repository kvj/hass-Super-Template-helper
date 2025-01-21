
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import text

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("text", _Entity))
    return True

class _Entity(BaseEntity, text.TextEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def mode(self):
        return self.data("mode")

    @property
    def native_max(self):
        return self.data("max")

    @property
    def native_min(self):
        return self.data("min")

    @property
    def pattern(self):
        return self.data("pattern")

    @property
    def native_value(self):
        return self.data("value")

    async def async_set_value(self, value: str) -> None:
        return await self.coordinator.async_execute_action("on_set", {"value": value})
