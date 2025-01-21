
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import scene

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("scene", _Entity))
    return True

class _Entity(BaseEntity, scene.Scene):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    async def async_activate(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_activate", kwargs)
