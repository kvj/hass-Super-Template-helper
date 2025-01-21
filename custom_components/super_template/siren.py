
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import siren

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("siren", _Entity))
    return True

class _Entity(BaseEntity, siren.SirenEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def is_on(self):
        return self.data("value")

    @property
    def available_tones(self):
        return self.data("available_tones")

    @property
    def supported_features(self):
        return self.data_as_or("supported_features", siren.const.SirenEntityFeature)

    async def async_turn_on(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_turn_on", kwargs)

    async def async_turn_off(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_turn_off", kwargs)
