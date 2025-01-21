
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import notify

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("notify", _Entity))
    return True

class _Entity(BaseEntity, notify.NotifyEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def supported_features(self):
        return self.data_as_or("supported_features", notify.NotifyEntityFeature)

    async def async_send_message(self, message: str, title: str | None = None):
        return await self.coordinator.async_execute_action("on_message", {
            "message": message,
            "title": title,
        })
