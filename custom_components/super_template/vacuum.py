
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import vacuum

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("vacuum", _Entity))
    return True

class _Entity(BaseEntity, vacuum.StateVacuumEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def state(self):
        return self.data("value", vacuum.const.STATE_DOCKED)

    @property
    def battery_icon(self):
        return self.data("battery_icon")

    @property
    def battery_level(self):
        return self.data("battery_level")

    @property
    def fan_speed(self):
        return self.data("fan_speed")

    @property
    def fan_speed_list(self):
        return self.data("fan_speed_list")

    @property
    def supported_features(self):
        return self.data_as_or("supported_features", vacuum.VacuumEntityFeature)
    
    async def async_stop(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_stop", kwargs)

    async def async_return_to_base(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_return", kwargs)

    async def async_clean_spot(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_clean_spot", kwargs)

    async def async_locate(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_locate", kwargs)

    async def async_set_fan_speed(self, fan_speed: str, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_fan_speed", kwargs)

    async def async_send_command(self, command: str, params = None, **kwargs,) -> None:
        return await self.coordinator.async_execute_action("on_command", {
            "command": command,
            "params": params if params else {},
            **kwargs,
        })

    async def async_start(self) -> None:
        return await self.coordinator.async_execute_action("on_start")

    async def async_pause(self) -> None:
        return await self.coordinator.async_execute_action("on_pause")
