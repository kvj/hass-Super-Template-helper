DOMAIN = "super_template"
PLATFORMS = ["sensor", "binary_sensor", "switch", "button"]

CONF_TEMPLATE = "__template"
CONF_NAME = "__name"

COMMON_PROPS = ("value", "icon", "device_class", "entity_category", "available", "unit_of_measurement")

DOMAIN_PROPS = {
    "sensor": ("display_precision", "state_class"),
    "light": ("brightness", "color_mode", "rgb_color", "rgbw_color", "rgbww_color", "supported_color_modes"),
    "select": ("options",),
}
