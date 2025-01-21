
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.const import (
    UnitOfTemperature,
)

from homeassistant.components import climate

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("climate", _Entity))
    return True

class _Entity(BaseEntity, climate.ClimateEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def current_temperature(self):
        return self.data("current_temperature")
    
    @property
    def hvac_action(self):
        return self.data_as_enum("hvac_action", climate.const.HVACAction)
    
    @property
    def hvac_mode(self):
        return self.data_as_enum("value", climate.const.HVACMode)

    @property
    def hvac_modes(self):
        return self.data_as_enum_list("hvac_modes", climate.const.HVACMode, default=climate.const.HVACMode.OFF)

    @property
    def min_temp(self):
        return self.data("min_temp")

    @property
    def max_temp(self):
        return self.data("max_temp")

    @property
    def preset_mode(self):
        return self.data("preset_mode")

    @property
    def preset_modes(self):
        return self.data("preset_modes")

    @property
    def target_temperature(self):
        return self.data("target_temperature")

    @property
    def target_temperature_high(self):
        return self.data("target_temperature_high")

    @property
    def target_temperature_low(self):
        return self.data("target_temperature_low")
    
    @property
    def temperature_unit(self):
        return self.data("unit_of_measurement", UnitOfTemperature.CELSIUS)

    @property
    def supported_features(self):
        default = climate.const.ClimateEntityFeature.TURN_ON | climate.const.ClimateEntityFeature.TURN_OFF
        return self.data_as_or("supported_features", climate.const.ClimateEntityFeature, default)

    async def async_set_hvac_mode(self, hvac_mode):
        return await self.coordinator.async_execute_action("on_mode", {"mode": hvac_mode})

    async def async_turn_on(self):
        return await self.coordinator.async_execute_action("on_turn_on")

    async def async_turn_off(self):
        return await self.coordinator.async_execute_action("on_turn_off")

    async def async_set_preset_mode(self, preset_mode):
        return await self.coordinator.async_execute_action("on_preset", {"preset": preset_mode})

    async def async_set_temperature(self, **kwargs):
        return await self.coordinator.async_execute_action("on_temperature", kwargs)
