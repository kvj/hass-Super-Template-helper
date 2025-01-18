
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import switch

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("switch", _Entity))
    return True

class _Entity(BaseEntity, switch.SwitchEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def device_class(self):
        if value := self.coordinator.data.get("device_class"):
            return switch.SwitchDeviceClass(value)
    
    @property
    def is_on(self):
        return self.coordinator.data.get("value")
    
    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_execute_action("on_turn_on", kwargs)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_execute_action("on_turn_off", kwargs)
