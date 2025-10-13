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
        BaseEntity.__init__(self, coordinator)
        image.ImageEntity.__init__(self, coordinator.hass)
        self._last_url = None

    @property
    def content_type(self):
        return self.coordinator.data.get("content_type")

    @property
    def image_url(self):
        return self.coordinator.data.get("url")

    @property
    def image_last_updated(self):
        value = self.coordinator.data.get("value") 
        url = self.coordinator.data.get("url")
        if url != self._last_url:
            self._cached_image = None
            self._last_url = url
        self._cached_image = None
        if value and isinstance(value, str):
            return datetime.fromisoformat(value)
        if value and isinstance(value, float):
            return datetime.fromtimestamp(value)
        return None
