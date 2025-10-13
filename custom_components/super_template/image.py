from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import image

import logging

from .coordinator import BaseEntity, Coordinator

from datetime import datetime

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("image", _Entity))
    return True

class _Entity(BaseEntity, image.ImageEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def content_type(self):
        return self.coordinator.data.get("content_type")

    @property
    def image_url(self):
        return self.coordinator.data.get("url")

    @property
    def last_updated(self):
        value = self.coordinator.data.get("value") 
        if value and isinstance(value, str):
            return datetime.fromisoformat(value)
        if value and isinstance(value, float):
            return datetime.fromtimestamp()
        return None
