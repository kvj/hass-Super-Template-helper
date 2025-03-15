
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.components import event

import logging

from .coordinator import BaseEntity, Coordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator], add_entities):
    coordinator = entry.runtime_data
    add_entities(coordinator.forward_setup("event", _Entity))
    return True

class _Entity(BaseEntity, event.EventEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    @property
    def event_types(self):
        return self.coordinator.data.get("types")

    async def async_added_to_hass(self) -> None:
        self.coordinator.add_event_listener(self)

    async def async_will_remove_from_hass(self) -> None:
        self.coordinator.remove_event_listener(self)

    async def async_on_event(self, name: str, data: dict):
        if name in self.event_types:
            self._trigger_event(name, {**data})
        else:
            _LOGGER.warning(f"async_on_event: unsupported event: {name} with {data}")
