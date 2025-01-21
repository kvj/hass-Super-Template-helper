
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import cover

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("cover", _Entity))
    return True

class _Entity(BaseEntity, cover.CoverEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def device_class(self):
        return self.data_as_enum("device_class", cover.CoverDeviceClass)

    @property
    def current_cover_position(self):
        return self.data("current_cover_position")

    @property
    def is_closed(self):
        return self.data("value")

    @property
    def is_closing(self):
        return self.data("is_closing")

    @property
    def is_opening(self):
        return self.data("is_opening")

    @property
    def supported_features(self):
        return self.data_as_or("supported_features", cover.CoverEntityFeature)


    async def async_open_cover(self, **kwargs):
        return await self.coordinator.async_execute_action("on_open", kwargs)

    async def async_close_cover(self, **kwargs):
        return await self.coordinator.async_execute_action("on_close", kwargs)

    async def async_set_cover_position(self, **kwargs):
        return await self.coordinator.async_execute_action("on_position", kwargs)

    async def async_stop_cover(self, **kwargs):
        return await self.coordinator.async_execute_action("on_stop", kwargs)
