from homeassistant.core import HomeAssistant, Context
from homeassistant.exceptions import HomeAssistantError
from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from homeassistant.helpers import (
    dispatcher,
    event,
    template,
    device_registry,
    area_registry,
    entity_registry,
    script,
    storage,
    config_validation,
    trigger,
)
from homeassistant.util import (
    dt,
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

async def async_get_arguments(hass: HomeAssistant, config: dict):
    config = config.get(SCHEMA_ARGUMENTS, {})
    return {key: (value if value else {}) for key, value in config.items()}

def __multiple_maybe(value, callback):
    if isinstance(value, list):
        result = []
        for item in value:
            if val := callback(item):
                result.append(val)
        return result
    elif val := callback(value):
        return val
    return None

def __entity_selector(hass: HomeAssistant, value, only_defined: bool, entity_ids: set):
    if isinstance(value, list):
        result = []
        for item in value:
            entity_ids.add(item)
            val = hass.states.get(item)
            if val and val.state in ('unknown', 'undefined') and only_defined:
                continue
            if val:
                result.append(val)
        return result
    if isinstance(value, str):
        entity_ids.add(value)
        if val := hass.states.get(value):
            return val
    return None

def __area_selector(hass: HomeAssistant, value):
    def cb(value):
        if area := area_registry.async_get(hass).async_get_area(value):
            return {"id": area.id, "name": area.name, "normalized_name": area.normalized_name, "icon": area.icon}
        return None
    return __multiple_maybe(value, cb)

def __device_selector(hass: HomeAssistant, value):
    def cb(value):
        if val := device_registry.async_get(hass).async_get(value):
            return {
                "device_name": val.name_by_user if val.name_by_user else val.name,
                **val.dict_repr, 
            }
        return None
    return __multiple_maybe(value, cb)

def __config_entry_selector(hass: HomeAssistant, value):
    def cb(value):
        if val := hass.config_entries.async_get_entry(value):
            return val.as_dict()
        return None
    return __multiple_maybe(value, cb)

def _convert_argument(hass: HomeAssistant, key: str, value, selector: dict, only_defined: bool, result: dict, entity_ids: set = set()):
    _LOGGER.debug(f"_convert_argument: input: {key}, {value}, {selector}")
    if "entity" in selector:
        result[f"__{key}"] = value
        value = __entity_selector(hass, value, only_defined, entity_ids)
    if "device" in selector:
        result[f"__{key}"] = value
        value = __device_selector(hass, value)
    if "config_entry" in selector:
        result[f"__{key}"] = value
        value = __config_entry_selector(hass, value)
    if "area" in selector:
        result[f"__{key}"] = value
        value = __area_selector(hass, value)
    if "template" in selector and isinstance(value, str):
        result[f"__{key}"] = value
        tmpl = template.Template(value, hass)
        try:
            entity_ids.update(tmpl.async_render_to_info(variables={}).entities)
        except:
            _LOGGER.info(f"_convert_argument: failed to render template info: {value}")
        value = tmpl.async_render(result)
    result[key] = value
    return (result, entity_ids)

def _extract_arguments(variables: dict, config: dict):
    return [(key, config.get(key), obj.get("selector", {}), obj.get("static") == True, obj.get("defined") == True) for key, obj in variables.items()]

def _build_context(hass: HomeAssistant, variables: dict, config: dict):
    result = {}
    entity_ids = set()
    for key, value, selector, is_static, only_defined in _extract_arguments(variables, config):
        if is_static:
            result, _ = _convert_argument(hass, key, value, selector, only_defined, result, set())
        else:
            result, entity_ids = _convert_argument(hass, key, value, selector, only_defined, result, entity_ids)
    _LOGGER.debug(f"_build_context: {config}, {result}, {entity_ids}")
    return (result, entity_ids)

async def async_render_name(hass: HomeAssistant, id: str, config: dict):
    tmpl = await async_get_template(hass, id)
    ctx, _ = _build_context(hass, await async_get_arguments(hass, tmpl), config)
    tmpl = template.Template(tmpl.get("name", "").strip(), hass)
    return tmpl.async_render(ctx)

class Coordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            setup_method=self._async_setup,
            update_method=self._async_update,
            update_interval=timedelta(minutes=1),
            always_update=False,
        )
        self._entry = entry
        self._entry_id = entry.entry_id

        self._on_entity_state_handler = None
        self._trigger_handlers = []
        self._template = None
        self._storage = storage.Store[dict](hass, 1, f"{DOMAIN}.{self._entry_id}")
        self._event_listeners = []

    async def async_build_entity_template(self, config: dict, variables: dict):
        result = {SCHEMA_ATTRS: {}}
        entity_ids = set()
        result[SCHEMA_VARIABLES] = self._templatify(config.get(SCHEMA_VARIABLES, {}))
        ctx = await self.async_extend_context(variables, result[SCHEMA_VARIABLES], suppress_errors=True)
        def _template_to_entity_ids(tmpl: template.Template):
            entity_ids.update(tmpl.async_render_to_info(variables=ctx).entities)
        for key in COMMON_PROPS + DOMAIN_PROPS.get(config.get("type"), ()):
            if key in config:
                if isinstance(config[key], str):
                    result[key] = template.Template(config[key].strip(), self.hass)
                    _template_to_entity_ids(result[key])
                else:
                    result[key] = config[key]
        for key, value in config.get(SCHEMA_ATTRS, {}).items():
            if isinstance(value, str):
                result[SCHEMA_ATTRS][key] = template.Template(value.strip(), self.hass)
                _template_to_entity_ids(result[SCHEMA_ATTRS][key])
            else:
                result[SCHEMA_ATTRS][key] = value
        for key, obj in config.items():
            if key.startswith("on_") and obj:
                if "actions" in obj and "template" in obj:
                    actions = obj["actions"]
                    result[key] = self._templatify(actions) if obj["template"] != False else actions
                else:
                    result[key] = self._templatify(obj)
            if key.startswith("when_") and obj:
                result[key] = self._templatify(obj)
        return (result, entity_ids)
    
    def _templatify(self, obj):
        def _one_object(obj):
            if isinstance(obj, list):
                return [_one_object(item) for item in obj]
            if isinstance(obj, dict):
                return {
                    key: _one_object(item) for key, item in obj.items()
                }
            if isinstance(obj, str):
                sobj = obj.strip()
                if sobj.startswith(r"{{{") and sobj.endswith(r"}}}"):
                    return sobj[1:-1]
                return template.Template(sobj, self.hass)
            return obj
        return _one_object(obj)
    
    def _apply_templates(self, obj, variables: dict):
        def _one_object(obj):
            if isinstance(obj, list):
                return [_one_object(item) for item in obj]
            if isinstance(obj, dict):
                return {key: _one_object(item) for key, item in obj.items()}
            if isinstance(obj, template.Template):
                return obj.async_render(variables=variables)
            return obj
        return _one_object(obj)
    
    async def _async_setup(self): # Startup
        self.data = {}

    async def _async_update(self): # Every second or update_interval
        if not self.template_loaded():
            return self.data
        data_, changed = await self._async_update_entity(self._template, self._entity_tmpl, op="timer")
        return data_ if changed else self.data

    def _update_state(self, data: dict):
        _LOGGER.debug(f"_update_state: new state: {data}")
        self.async_set_updated_data({
            **self.data,
            **data,
        })

    async def _async_on_state_change(self, event):
        entity_id = event.data["entity_id"]
        _LOGGER.debug(f"_async_on_state_change: {entity_id}, {event}")
        if self.template_loaded():
            new_state, changed = await self._async_update_entity(self._template, self._entity_tmpl, op="state")
            if new_state != self.data and changed:
                self._update_state(new_state)
    
    def state_by_entity_id(self, entity_id: str | None):
        return self.hass.states.get(entity_id) if entity_id else None

    def load_options(self):
        self._config = self._entry.as_dict()["options"]

    async def async_extend_context(self, context: dict, variables: dict, suppress_errors = False):
        result = { **context }
        self_entities = entity_registry.async_entries_for_config_entry(entity_registry.async_get(self.hass), self._entry_id)
        if len(self_entities):
            result["_entity_id"] = self_entities[0].entity_id
            result["_this"] = self.hass.states.get(self_entities[0].entity_id)
            
        if stored_state_ := await self._storage.async_load():
            result["_state"] = stored_state_
        else:
            result["_state"] = {}

        for key, value in variables.items():
            value_ = value
            if suppress_errors:
                try:
                    value_ = self._apply_templates(value, result)
                except template.TemplateError:
                    value_ = None
            else:
                value_ = self._apply_templates(value, result)
            result[key] = value_
            if isinstance(value_, dict) and "selector" in value_:
                result, _ = _convert_argument(self.hass, key, value_.get("value"), value_.get("selector"), False, result)
            _LOGGER.debug(f"async_extend_context: variable {key} = {result[key]}, {type(result[key])}")
        return result

    async def _async_update_entity(self, config: dict, entity_tmpl: dict, op: str = "other"):
        if "on_before_update" in entity_tmpl:
            await self.async_execute_action("on_before_update", {"op": op})
        ctx, _ = _build_context(self.hass, await async_get_arguments(self.hass, config), self._config)
        ctx = await self.async_extend_context(ctx, entity_tmpl.get(SCHEMA_VARIABLES, {}))
        if "changed" in entity_tmpl:
            is_changed = self._apply_templates(entity_tmpl["changed"], ctx)
            if is_changed == False:
                return None, False
        result = {}
        for key, value in entity_tmpl.items():
            if key in (SCHEMA_VARIABLES, SCHEMA_ATTRS) or key.startswith("on_"):
                continue
            result[key] = self._apply_templates(value, ctx)
        result[SCHEMA_ATTRS] = self._apply_templates(entity_tmpl[SCHEMA_ATTRS], ctx)
        if "available" not in result:
            result["available"] = True
        if "on_update" in entity_tmpl:
            await self.async_execute_action("on_update", {"op": op})
        _LOGGER.debug(f"_async_update_entity: {config}[{op}] with {ctx} = {result}")
        return result, True
    
    async def _async_create_trigger(self, name: str, config, ctx: dict):
        trigger_conf = self._apply_templates(config, ctx)
        trigger_ = config_validation.TRIGGER_SCHEMA(trigger_conf)
        validated_trigger = await trigger.async_validate_trigger_config(self.hass, trigger_)
        _LOGGER.debug(f"_async_create_trigger: {name} / {trigger_conf} / {trigger_} / {validated_trigger}")
        async def on_trigger_(trigger_vars, trigger_ctx):
            _LOGGER.debug(f"_async_create_trigger::on_trigger_: {name} / {trigger_} with {trigger_vars} and {trigger_ctx}")
            if self.template_loaded():
                new_state, changed = await self._async_update_entity(self._template, self._entity_tmpl, op=name)
                if new_state != self.data and changed:
                    self._update_state(new_state)
                handler_name = f"on_{name}_trigger"
                if handler_name in self._entity_tmpl:
                    _LOGGER.debug(f"_async_create_trigger::on_trigger_ call handler {handler_name} with {trigger_vars}")
                    await self.async_execute_action(handler_name, trigger_vars)
        remove_cb = await trigger.async_initialize_triggers(
            self.hass, validated_trigger, on_trigger_, domain=DOMAIN, name=name, log_cb=_LOGGER.log,
        )
        return remove_cb
    
    async def async_load(self):
        self.load_options()
        _LOGGER.debug(f"async_load: {self._config}")
        self._template_name = self._config[CONF_TEMPLATE]
        self._template = await async_get_template(self.hass, self._template_name)
        arguments = await async_get_arguments(self.hass, self._template)
        ctx, var_entity_ids = _build_context(self.hass, arguments, self._config)
        entity_tmpl, entity_ids = await self.async_build_entity_template(self._template, ctx)
        _LOGGER.debug(f"async_load: entity IDs: {entity_ids}, {var_entity_ids}")
        entity_ids.update(var_entity_ids)
        self._entity_tmpl = entity_tmpl

        update_every_ = timedelta(minutes=1)
        if SCHEMA_UPDATE_INTERVAL in self._template:
            if td := dt.parse_duration(self._template[SCHEMA_UPDATE_INTERVAL]):
                update_every_ = td
        self.update_interval = update_every_
        try:
            data_, changed = await self._async_update_entity(self._template, self._entity_tmpl, op="startup")
            if changed:
                self._update_state(data_)
        except:
            _LOGGER.exception(f"async_load: failed to update state at the startup: {self._config}")
            self._update_state({"available": False})
        _LOGGER.info(f"async_load: configured with config = {self._config}, initial state = {self.data}, entity ids = {entity_ids}, update every = {self.update_interval}")
        if len(entity_ids):
            self._on_entity_state_handler = event.async_track_state_change_event(
                self.hass, entity_ids, action=self._async_on_state_change
            )
        for key, value in entity_tmpl.items():
            if key.startswith("when_") and value:
                self._trigger_handlers.append(await self._async_create_trigger(key, value, ctx))
        for key, value, selector, _, _ in _extract_arguments(arguments, self._config):
            if "trigger" in selector and value:
                self._trigger_handlers.append(await self._async_create_trigger(key, value, ctx))

    def _disable_listener(self, listener):
        if listener:
            listener()
        return None

    async def async_unload(self):
        _LOGGER.debug(f"async_unload:")
        self._on_entity_state_handler = self._disable_listener(self._on_entity_state_handler)
        self._template = None
        [self._disable_listener(cb) for cb in self._trigger_handlers]
        self._trigger_handlers = []
        self._event_listeners = []

    def forward_setup(self, domain: str, entity_cls):
        if self.template_loaded() and self._template.get("type") == domain:
            return [entity_cls(self)]
        return []
    
    async def _async_execute_actions(self, name: str, extra: dict, actions):
        ctx, _ = _build_context(self.hass, await async_get_arguments(self.hass, self._template), self._config)
        if extra:
            ctx = {
                **extra,
                **ctx,
            }
        ctx = await self.async_extend_context(ctx, self._entity_tmpl.get(SCHEMA_VARIABLES, {}))
        context = Context()
        actions_ = config_validation.SCRIPT_SCHEMA(self._apply_templates(actions, ctx))
        script_ = script.Script(self.hass, actions_, f"_st_{self._entry_id}_{name}", DOMAIN, top_level=True)
        _LOGGER.debug(f"_async_execute_actions: {name} with {ctx} and {extra} and actions {actions_}")
        result = await script_.async_run(context=context, run_variables=ctx)
        _LOGGER.debug(f"_async_execute_actions: result: {name} = {result}")
        if result and isinstance(result.service_response, dict):
            _LOGGER.debug(f"_async_execute_actions: storing state: {result.service_response}")
            return result.service_response
        return None
    
    async def async_execute_action(self, name: str, extra: dict = {}):
        if not self.template_loaded():
            return
        if name not in self._template:
            _LOGGER.warning(f"async_execute_action: not configured action: {name}, with extra {extra}")
            return
        actions = self._entity_tmpl[name]
        result = await self._async_execute_actions(name, extra, actions)
        if result and isinstance(result, dict):
            _LOGGER.debug(f"async_execute_action: storing state: {result}")
            await self._storage.async_save(result)
            if self._template.get("optimistic") == False:
                new_state, changed = await self._async_update_entity(self._template, self._entity_tmpl, op="after_state")
                if new_state != self.data and changed:
                    self._update_state(new_state)
        return result
    
    async def async_call_argument_action(self, name: str, extra: dict):
        if not self.template_loaded():
            return
        arguments = await async_get_arguments(self.hass, self._template)
        ctx, _ = _build_context(self.hass, arguments, self._config)
        actions = ctx.get(name)
        _LOGGER.debug(f"async_call_argument_action: {name} = {actions}, {extra}")
        if actions:
            return await self._async_execute_actions(name, extra, actions)
        _LOGGER.debug(f"async_call_argument_action: {name} is empty")
        return None

    async def async_fire_event(self, name: str, extra: dict):
        if not self.template_loaded():
            return None
        _LOGGER.debug(f"async_fire_event: {name} with {extra}")
        for l in self._event_listeners:
            await l.async_on_event(name, extra)
        return None

    def template_loaded(self) -> bool:
        if self._template and "type" in self._template:
            return True
        return False

    def add_event_listener(self, listener):
        self._event_listeners.append(listener)

    def remove_event_listener(self, listener):
        if listener in self._event_listeners:
            self._event_listeners.remove(listener)

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
        super_value = super().state_attributes
        return {
            **(super_value if super_value else {}),
            **self.coordinator.data.get(SCHEMA_ATTRS, {})
        }
    
    def data(self, name: str, default=None):
        return self.coordinator.data.get(name, default)
    
    def data_as_enum(self, name: str, cls, default=None):
        if val := self.data(name):
            return cls(val).value
        return default

    def data_as_tuple(self, name: str, cls, default=None):
        if val := self.data(name):
            if isinstance(val, list):
                return tuple(val)
        return default

    def data_as_enum_list(self, name: str, cls, default=None):
        if val := self.data(name):
            if isinstance(val, list):
                return [cls(item).value for item in val]
            else:
                return [cls(val).value]
        return [default]

    def data_as_or(self, name: str, cls, default=0):
        if val := self.data(name):
            if isinstance(val, list):
                result = cls(0)
                for item in val:
                    result |= cls._member_map_.get(item, 0)
                _LOGGER.debug(f"data_as_or: {result}, {cls._member_map_}, {val}")
                return result
            else:
                return cls._member_map_.get(val, 0)
        return cls(default)
    
    async def async_on_event(self, name: str, data: dict):
        pass
