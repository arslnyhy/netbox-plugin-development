from netbox.plugins import PluginConfig

class NetBoxConfigValidatorConfig(PluginConfig):
    name = 'netbox_config_validator'
    verbose_name = 'NetBox Config Validator'
    description = 'Detect device config drift between intent and reality'
    version = '0.1'
    base_url = 'config-validator'

config = NetBoxConfigValidatorConfig