DOMAIN = "super_template"
PLATFORMS = ["sensor", "binary_sensor", "switch", "button"]

CONF_TEMPLATE = "__template"
CONF_NAME = "__name"

SCHEMA_ARGUMENTS = "arguments"
SCHEMA_VARIABLES = "variables"
SCHEMA_ATTRS = "attrs"
SCHEMA_UPDATE_INTERVAL = "update_interval"

COMMON_PROPS = ("value", "icon", "device_class", "entity_category", "available", "unit_of_measurement")

DOMAIN_PROPS = {
    "sensor": ("display_precision", "state_class", "options"),
    "light": ("brightness", "color_mode", "rgb_color", "rgbw_color", "rgbww_color", "supported_color_modes"),
    "select": ("options",),
}
