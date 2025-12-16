from setuptools import find_packages, setup

setup(
    name='netbox-config-validator',
    version='0.1',
    description='An example NetBox plugin',
    install_requires=['netmiko'],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'netbox_config_validator': ['templates/**/*.html'],
    },
    zip_safe=False,
)