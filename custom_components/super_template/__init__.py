from __future__ import annotations
from .constants import *

from .coordinator import Coordinator

from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.config_entries import ConfigEntry
from homeassistant.loader import async_get_integration
from homeassistant.helpers.typing import ConfigType

from homeassistant.helpers import service, reload
from homeassistant.const import SERVICE_RELOAD


import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

_SIMPLE_VALUE = vol.Any(str, bool, int, float)
_COMPLEX_VALUE = vol.Any(str, bool, int, float, dict, list)

_ARG_SCHEMA = vol.Schema({
    vol.Optional("optional"): bool,
    vol.Optional("static"): bool,
    vol.Optional("defined"): bool,
    vol.Optional("selector"): vol.Schema({}, extra=vol.ALLOW_EXTRA),
    vol.Optional("description"): str,
    vol.Optional("default"): _SIMPLE_VALUE
})

_TMPL_SCHEMA = vol.Schema({
    vol.Required("type"): vol.Any(*PLATFORMS),
    vol.Optional("title"): str,
    vol.Optional("optimistic", default=True): bool,
    vol.Required("name"): str,
    vol.Optional("icon"): str,
    vol.Optional("value"): str,
    vol.Optional("unit_of_measurement"): str,
    vol.Optional(SCHEMA_ATTRS): {str: _SIMPLE_VALUE},
    vol.Optional(SCHEMA_ARGUMENTS): {str: _ARG_SCHEMA},
    vol.Optional(SCHEMA_VARIABLES): {str: _COMPLEX_VALUE},
    vol.Optional(SCHEMA_UPDATE_INTERVAL): str,
}, extra=vol.ALLOW_EXTRA)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({str: _TMPL_SCHEMA}, extra=vol.ALLOW_EXTRA),
}, extra=vol.ALLOW_EXTRA)

async def _async_update_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator]):
    _LOGGER.debug(f"_async_update_entry: {entry}")
    coordinator = entry.runtime_data
    await coordinator.async_unload()
    await coordinator.async_load()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator]):

    coordinator = Coordinator(hass, entry)
    entry.runtime_data = coordinator

    entry.async_on_unload(entry.add_update_listener(_async_update_entry))
    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_load()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry[Coordinator]):
    coordinator = entry.runtime_data

    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await coordinator.async_unload()
    entry.runtime_data = None
    return True

async def _async_reload_entries(hass: HomeAssistant):
    entries = hass.config_entries.async_entries(DOMAIN, False, False)
    for entry in entries:
        if coordinator := entry.runtime_data:
            await coordinator.async_unload()
            await coordinator.async_load()

def _register_coordinator_service(hass: HomeAssistant,  name: str, handler, resp: SupportsResponse = SupportsResponse.NONE):
    async def handler_(call):
        for entry_id in await service.async_extract_config_entry_ids(hass, call):
            if entry := hass.config_entries.async_get_entry(entry_id):
                _LOGGER.debug(f"_register_coordinator_service: {name}: {entry.domain}")
                if entry.domain == DOMAIN:
                    await handler(entry.runtime_data, call.data)
    hass.services.async_register(DOMAIN, name, handler_, supports_response=resp)
    

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    cmp = await async_get_integration(hass, DOMAIN)
    ver = cmp.manifest["version"]

    conf = config.get(DOMAIN, {})
    _LOGGER.debug(f"async_setup: {ver}, {conf}")
    hass.data[DOMAIN] = conf
    async def _async_reload_yaml(call):
        config = await reload.async_integration_yaml_config(hass, DOMAIN)
        conf = config.get(DOMAIN, {})
        _LOGGER.debug(f"_async_reload_yaml: {conf}")
        hass.data[DOMAIN] = conf
        await _async_reload_entries(hass)
    service.async_register_admin_service(hass, DOMAIN, SERVICE_RELOAD, _async_reload_yaml)
    async def _call_argument_action(c: Coordinator, data: dict):
        return await c.async_call_argument_action(data["argument"], data.get("extra", {}))
    _register_coordinator_service(hass, "call_argument_action", _call_argument_action, resp=SupportsResponse.OPTIONAL)
    async def _call_action(c: Coordinator, data: dict):
        return await c.async_execute_action(f"on_{data["action"]}", data.get("extra", {}))
    _register_coordinator_service(hass, "call_action", _call_action, resp=SupportsResponse.OPTIONAL)
    async def _fire_event(c: Coordinator, data: dict):
        return await c.async_fire_event(data["name"], data.get("extra", {}))
    _register_coordinator_service(hass, "fire_event", _fire_event, resp=SupportsResponse.OPTIONAL)
    return True
