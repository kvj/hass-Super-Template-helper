from collections.abc import Mapping
from typing import Any, cast

from homeassistant import config_entries
from homeassistant.core import (
    async_get_hass,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector

# from homeassistant.const import (
# )

from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
    SchemaFlowError,
    SchemaCommonFlowHandler,
)

from .constants import (
    DOMAIN,
    CONF_TEMPLATE,
    CONF_NAME,
)

from .coordinator import (
    async_get_templates,
    async_get_arguments,
    async_render_name,
    async_get_template,
)

import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): selector({"text": {}}),
})

async def _build_config_schema(step: SchemaCommonFlowHandler):
    config = await async_get_template(async_get_hass(), step.options[CONF_TEMPLATE])
    variables = await async_get_arguments(async_get_hass(), config)
    schema = {}
    for key, obj in variables.items():
        selector_ = obj.get("selector", {"text": {}})
        if obj.get("optional") == True:
            schema[vol.Optional(key, default=obj.get("default"))] = selector(selector_)
        else:
            schema[vol.Required(key, default=obj.get("default"))] = selector(selector_)
    _LOGGER.debug(f"_build_user_schema: {step.options}, {step.flow_state}, {schema}")
    return vol.Schema(schema)

async def _build_user_schema(step):
    _LOGGER.debug(f"_build_user_schema:")
    templates = await async_get_templates(async_get_hass())
    options = [{"value": x[0], "label": x[1]} for x in templates]
    return vol.Schema({
        vol.Required(CONF_TEMPLATE): selector({"select": {"options": options}})
    })

async def _validate_config(step, user_input):
    user_input[CONF_TEMPLATE] = step.options[CONF_TEMPLATE]
    user_input[CONF_NAME] = await async_render_name(async_get_hass(), user_input[CONF_TEMPLATE], user_input)

    _LOGGER.debug(f"_validate_config: {user_input}, {step.options}, {step.flow_state}")
    # raise SchemaFlowError("not_implemented")
    return user_input

async def _next_config_step(user_input):
    _LOGGER.debug(f"_next_config_step: {user_input}")
    return "config"

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(_build_user_schema, next_step=_next_config_step),
    "config": SchemaFlowFormStep(_build_config_schema, validate_user_input=_validate_config),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(_build_config_schema, _validate_config),
}

class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        return cast(str, options[CONF_NAME])
