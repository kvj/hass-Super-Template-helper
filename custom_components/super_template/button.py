
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import button

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("button", _Entity))
    return True

class _Entity(BaseEntity, button.ButtonEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def device_class(self):
        return self.data_as_enum("device_class", button.ButtonDeviceClass)

    async def async_press(self) -> None:
        return await self.coordinator.async_execute_action("on_press", {})
