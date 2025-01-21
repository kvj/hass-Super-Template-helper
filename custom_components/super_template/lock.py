
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import lock

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("lock", _Entity))
    return True

class _Entity(BaseEntity, lock.LockEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def changed_by(self):
        return self.data("changed_by")

    @property
    def code_format(self):
        return self.data("code_format")

    @property
    def is_locked(self):
        return self.data("value")

    @property
    def is_locking(self):
        return self.data("is_locking")

    @property
    def is_unlocking(self):
        return self.data("is_unlocking")

    @property
    def is_jammed(self):
        return self.data("is_jammed")

    @property
    def is_opening(self):
        return self.data("is_opening")

    @property
    def is_open(self):
        return self.data("is_open")

    @property
    def supported_features(self):
        return self.data_as_or("supported_features", lock.LockEntityFeature)

    async def async_lock(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_lock", kwargs)

    async def async_unlock(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_unlock", kwargs)

    async def async_open(self, **kwargs) -> None:
        return await self.coordinator.async_execute_action("on_open", kwargs)
