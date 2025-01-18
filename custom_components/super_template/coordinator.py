from homeassistant.core import HomeAssistant, Context
from homeassistant.exceptions import HomeAssistantError

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from homeassistant.helpers import (
    dispatcher,
    event,
    template,
    device_registry,
    script,
)

from homeassistant.const import (
    EntityCategory,
)


from .constants import *

import collections.abc
import logging
import json, copy
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

async def async_get_templates(hass: HomeAssistant):
    config = hass.data.get(DOMAIN)
    if not config:
        return []
    _LOGGER.debug(f"async_get_templates: {config}")
    return [(key, obj.get("title", key)) for key, obj in config.items()]

async def async_get_template(hass: HomeAssistant, id: str):
    return hass.data.get(DOMAIN, {}).get(id, {})

async def async_get_variables(hass: HomeAssistant, config: dict):
    config = config.get("variables", {})
    return {key: (value if value else {}) for key, value in config.items()}

def _build_context(hass: HomeAssistant, variables: dict, config: dict):
    result = {}
    entity_ids = set()
    for key, obj in variables.items():
        value = config.get(key)
        if "entity" in obj.get("selector", {}) and value:
            entity_ids.add(value)
            value = hass.states.get(value)
        result[key] = value
    _LOGGER.debug(f"_build_context: {result}, {config}")
    return (result, entity_ids)

async def async_render_name(hass: HomeAssistant, id: str, config: dict):
    tmpl = await async_get_template(hass, id)
    ctx, _ = _build_context(hass, await async_get_variables(hass, tmpl), config)
    tmpl = template.Template(tmpl.get("name", ""), hass)
    return tmpl.async_render(ctx)

class Coordinator(DataUpdateCoordinator):

    def __init__(self, hass, entry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            setup_method=self._async_setup,
            update_method=self._async_update,
            update_interval=timedelta(seconds=1),
            always_update=False,
        )
        self._entry = entry
        self._entry_id = entry.entry_id

        self._on_entity_state_handler = None
        self._template = None

    def _build_entity_template(self, config: dict, variables: dict):
        result = {"attrs": {}}
        entity_ids = set()
        def _template_to_entity_ids(tmpl: template.Template):
            entity_ids.update(tmpl.async_render_to_info(variables=variables).entities)
        for key in COMMON_PROPS + DOMAIN_PROPS.get(config.get("type"), ()):
            if key in config:
                if isinstance(config[key], str):
                    result[key] = template.Template(config[key], self.hass)
                    _template_to_entity_ids(result[key])
                else:
                    result[key] = config[key]
        for key, value in config.get("attrs", {}).items():
            if isinstance(value, str):
                result["attrs"][key] = template.Template(value, self.hass)
            else:
                result["attrs"][key] = value
        return (result, entity_ids)
    
    def _object_with_templates(self, obj, variables: dict):
        def _one_object(obj):
            if isinstance(obj, list):
                return [_one_object(item) for item in obj]
            if isinstance(obj, dict):
                return {_one_object(key): _one_object(item) for key, item in obj.items()}
            if isinstance(obj, str):
                tmpl = template.Template(obj, self.hass)
                return tmpl.async_render(variables=variables)
            return obj
        return _one_object(obj)

    async def _async_setup(self): # Startup
        self.data = {}

    async def _async_update(self): # Every second
        if not self.template_loaded():
            return self.data
        return await self._async_update_entity(self._template, self._entity_tmpl)

    def _update_state(self, data: dict):
        _LOGGER.debug(f"_update_state: new state: {data}")
        self.async_set_updated_data({
            **self.data,
            **data,
        })

    async def _async_on_state_change(self, entity_id: str, from_state, to_state):
        _LOGGER.debug(f"_async_on_state_change: {entity_id}")
        new_state = await self._async_update_entity(self._template, self._entity_tmpl)
        if new_state != self.data:
            self._update_state(new_state)
    
    def state_by_entity_id(self, entity_id: str | None):
        return self.hass.states.get(entity_id) if entity_id else None

    def load_options(self):
        self._config = self._entry.as_dict()["options"]

    async def _async_update_entity(self, config: dict, entity_tmpl: dict):
        ctx, _ = _build_context(self.hass, await async_get_variables(self.hass, config), self._config)
        def _apply_tmpl_to_dict(tmpl: dict):
            result = {}
            for key, value in tmpl.items():
                if isinstance(value, template.Template):
                    result[key] = value.async_render(variables=ctx)
                else:
                    result[key] = value
            return result
        result = _apply_tmpl_to_dict(entity_tmpl)
        result["attrs"] = _apply_tmpl_to_dict(entity_tmpl["attrs"])
        return result
    
    async def async_load(self):
        self.load_options()
        _LOGGER.debug(f"async_load: {self._config}")
        self._template_name = self._config[CONF_TEMPLATE]
        self._template = await async_get_template(self.hass, self._template_name)
        ctx, var_entity_ids = _build_context(self.hass, await async_get_variables(self.hass, self._template), self._config)
        entity_tmpl, entity_ids = self._build_entity_template(self._template, ctx)
        _LOGGER.debug(f"async_load: entity IDs: {entity_ids}, {var_entity_ids}")
        entity_ids.update(var_entity_ids)
        self._entity_tmpl = entity_tmpl
        self._update_state(await self._async_update_entity(self._template, self._entity_tmpl))
        _LOGGER.info(f"async_load: configured with config = {self._config}, initial state = {self.data}")
        if len(entity_ids):
            self._on_entity_state_handler = event.async_track_state_change(
                self.hass, entity_ids, action=self._async_on_state_change
            )

    def _disable_listener(self, listener):
        if listener:
            listener()
        return None

    async def async_unload(self):
        _LOGGER.debug(f"async_unload:")
        self._on_entity_state_handler = self._disable_listener(self._on_entity_state_handler)
        self._template = None

    def forward_setup(self, domain: str, entity_cls):
        if self.template_loaded() and self._template.get("type") == domain:
            return [entity_cls(self)]
        return []
    
    async def async_execute_action(self, name: str, extra: dict):
        if not self.template_loaded():
            return
        if name not in self._template:
            _LOGGER.warning(f"async_execute_action: not configured action: {name}")
            return
        actions = self._template[name]
        if not isinstance(actions, list):
            actions = [actions]

        variables, _ = _build_context(self.hass, await async_get_variables(self.hass, self._template), self._config)
        if extra:
            variables = {
                **extra,
                **variables,
            }
        context = Context()
        actions = self._object_with_templates(actions, variables)
        script_ = script.Script(self.hass, actions, f"_st_{self._entry_id}_{name}", DOMAIN, top_level=False)
        _LOGGER.debug(f"async_execute_action: {name} with {variables} and {extra}")
        result = await script_.async_run(context=context)
        _LOGGER.debug(f"async_execute_action: result: {result}")

    def template_loaded(self) -> bool:
        if self._template and "type" in self._template:
            return True
        return False

class BaseEntity(CoordinatorEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)
        entry_id = self.coordinator._entry_id
        self._attr_unique_id = f"_st_{entry_id}"
        self._attr_has_entity_name = False
        self._attr_name = self.coordinator._config[CONF_NAME]

    @property
    def device_info(self):
        return {
            "identifiers": {
                ("config_entry", self.coordinator._entry_id)
            },
            "name": self.name,
        }
    
    @property
    def icon(self):
        return self.coordinator.data.get("icon")
    
    @property
    def available(self):
        if not self.coordinator.template_loaded():
            return False
        return self.coordinator.data.get("available") != False
    
    @property
    def unit_of_measurement(self):
        return self.coordinator.data.get("unit_of_measurement")
    
    @property
    def state_attributes(self):
        return self.coordinator.data.get("attrs", {})
