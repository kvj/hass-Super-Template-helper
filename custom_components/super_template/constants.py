DOMAIN = "super_template"
PLATFORMS = ["sensor", "binary_sensor", "switch", "button", "climate", "cover", "device_tracker", "light", "lock", "notify", "number", "scene", "select", "siren", "text", "valve", "vacuum", "water_heater"]

CONF_TEMPLATE = "__template"
CONF_NAME = "__name"

SCHEMA_ARGUMENTS = "arguments"
SCHEMA_VARIABLES = "variables"
SCHEMA_ATTRS = "attrs"
SCHEMA_UPDATE_INTERVAL = "update_interval"

COMMON_PROPS = ("value", "icon", "device_class", "entity_category", "available", "unit_of_measurement")

DOMAIN_PROPS = {
    "climate": ("current_temperature", "hvac_action", "hvac_modes", "max_temp", "min_temp", "preset_mode", "preset_modes", "target_temperature", "target_temperature_high", "target_temperature_low", "supported_features"), # value == hvac_mode
    "cover": ("current_cover_position", "is_closing", "is_opening", "supported_features"), # value == is_closed
    "device_tracker": ("battery_level", "latitude", "accuracy", "longitude", "source_type"), # value == location_name
    "light": ("brightness", "color_mode", "color_temp", "rgb_color", "rgbw_color", "rgbww_color", "supported_color_modes", "xy_color", "max_color_temp", "min_color_temp", "hs_color"),
    "lock": ("changed_by", "code_format", "is_locking", "is_unlocking", "is_jammed", "is_opening", "is_open", "supported_features"), # value == is_locked 
    "notify": ("supported_features",),
    "number": ("mode", "max_value", "min_value", "step"),
    "select": ("options",),
    "sensor": ("display_precision", "state_class", "options"),
    "siren": ("available_tones", "supported_features"),
    "text": ("mode", "max", "min", "pattern"),
    "valve": ("is_closed", "is_closing", "is_opening", "reports_position", "supported_features"), # current_valve_position == value
    "vacuum": ("battery_icon", "battery_level", "fan_speed", "fan_speed_list", "supported_features"), # state == value
    "water_heater": ("min_temp", "max_temp", "target_temperature", "target_temperature_high", "target_temperature_low", "current_temperature", "operation_list", "is_away_mode_on", "precision", "supported_features"), # current_operation == value
}
