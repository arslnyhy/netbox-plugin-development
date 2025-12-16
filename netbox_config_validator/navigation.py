from netbox.plugins import PluginMenuItem

menu_items = (
    PluginMenuItem(
        link='plugins:netbox_config_validator:drift_check',
        link_text='Config Validator',
        permissions=[],
    ),
)

