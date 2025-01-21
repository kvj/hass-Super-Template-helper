
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import water_heater

from homeassistant.const import (
    UnitOfTemperature,
    STATE_OFF,
)

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("water_heater", _Entity))
    return True

class _Entity(BaseEntity, water_heater.WaterHeaterEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def min_temp(self):
        return self.data("min_temp")

    @property
    def max_temp(self):
        return self.data("max_temp")

    @property
    def current_temperature(self):
        return self.data("current_temperature")

    @property
    def precision(self):
        return self.data("precision")

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
    def current_operation(self):
        return self.data("value", STATE_OFF)

    @property
    def operation_list(self):
        return self.data("operation_list")

    @property
    def is_away_mode_on(self):
        return self.data("is_away_mode_on")

    @property
    def supported_features(self):
        return self.data_as_or("supported_features", water_heater.WaterHeaterEntityFeature)

    async def async_set_temperature(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_temperature", kwargs)

    async def async_turn_on(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_turn_on", kwargs)

    async def async_turn_off(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_turn_off", kwargs)

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        return await self.coordinator.async_execute_action("on_mode", {"mode": operation_mode})

    async def async_turn_away_mode_on(self) -> None:
        return await self.coordinator.async_execute_action("on_away", {"on": True})

    async def async_turn_away_mode_off(self) -> None:
        return await self.coordinator.async_execute_action("on_away", {"on": False})
