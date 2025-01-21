
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import light

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("light", _Entity))
    return True

class _Entity(BaseEntity, light.LightEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def brightness(self):
        return self.data("brightness")

    @property
    def color_mode(self):
        return self.data_as_enum("color_mode", light.ColorMode)
    
    @property
    def supported_color_modes(self):
        if val := self.data_as_enum_list("supported_color_modes", light.ColorMode):
            return set(val)
        return None

    @property
    def max_color_temp_kelvin(self):
        return self.data("max_color_temp")
    
    @property
    def min_color_temp_kelvin(self):
        return self.data("min_color_temp")
    
    @property
    def color_temp_kelvin(self):
        return self.data("color_temp")
    
    @property
    def hs_color(self):
        return self.data_as_tuple("hs_color")
    
    @property
    def rgb_color(self):
        return self.data_as_tuple("rgb_color")
    
    @property
    def rgbw_color(self):
        return self.data_as_tuple("rgbw_color")
    
    @property
    def rgbww_color(self):
        return self.data_as_tuple("rgbww_color")
    
    @property
    def is_on(self):
        return self.data("value")

    async def async_turn_on(self, **kwargs):
        return await self.coordinator.async_execute_action("on_turn_on", kwargs)

    async def async_turn_off(self, **kwargs):
        return await self.coordinator.async_execute_action("on_turn_off", kwargs)
