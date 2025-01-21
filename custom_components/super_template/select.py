
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import select

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("select", _Entity))
    return True

class _Entity(BaseEntity, select.SelectEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def current_option(self):
        return self.data("value")

    @property
    def options(self):
        return self.data("options")

    async def async_select_option(self, option: str) -> None:
        return await self.coordinator.async_execute_action("on_set", {"option": option})
