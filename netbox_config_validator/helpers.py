"""
Helper functions for device connection and data collection.
"""
import os
from dotenv import load_dotenv
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

def connect_to_device(device_ip, username=USERNAME, password=PASSWORD, device_type='cisco_ios'):
    try:
        device_params = {
            'device_type': device_type,
            'host': device_ip,
            'username': username,
            'password': password,
            'timeout': 10,
        }
        
        connection = ConnectHandler(**device_params)
        return connection
        
    except NetmikoTimeoutException:
        return None
    except NetmikoAuthenticationException:
        return None
    except Exception:
        return None


def get_device_interfaces(connection):
    interfaces = {}
    
    try:
        output = connection.send_command('show ip interface brief')
        
        # Parse output line by line
        # Expected format: Interface IP-Address OK? Method Status Protocol
        for line in output.split('\n'):
            # Skip header lines and empty lines
            if 'Interface' in line or not line.strip():
                continue
            
            # Parse interface data using regex or split
            parts = line.split()
            if len(parts) >= 6:
                interface_name = parts[0]
                ip_address = parts[1] if parts[1] != 'unassigned' else None
                
                # Handle "administratively down" (two words) vs "up" or "down" (one word)
                if parts[4].lower() == 'administratively' and len(parts) >= 7:
                    status = 'admin down'
                    protocol = parts[6].lower()
                else:
                    status = parts[4].lower()
                    protocol = parts[5].lower()
                
                interfaces[interface_name] = {
                    'ip': ip_address,
                    'status': status,
                    'protocol': protocol,
                }
        
        return interfaces
        
    except Exception:
        return {}


def disconnect_device(connection):
    if connection:
        try:
            connection.disconnect()
        except Exception:
            pass


def compare_interfaces(netbox_interfaces, device_interfaces):
    """
    Compare NetBox interfaces with actual device interfaces to detect drift.
    """
    comparison = []
    
    # Get all interface names from both sources
    netbox_intf_dict = {intf.name: intf for intf in netbox_interfaces}
    device_intf_names = set(device_interfaces.keys())
    netbox_intf_names = set(netbox_intf_dict.keys())
    
    # Get all unique interface names from either NetBox or device
    all_interface_names = netbox_intf_names.union(device_intf_names)
    
    for intf_name in sorted(all_interface_names):
        in_netbox = intf_name in netbox_intf_names
        in_device = intf_name in device_intf_names
        
        result = {
            'name': intf_name,
            'in_netbox': in_netbox,
            'in_device': in_device,
            'netbox_enabled': None,
            'device_status': None,
            'device_protocol': None,
            'has_drift': False,
            'drift_reason': None,
        }
        
        # Get NetBox data
        if in_netbox:
            result['netbox_enabled'] = netbox_intf_dict[intf_name].enabled
        
        # Get device data
        if in_device:
            result['device_status'] = device_interfaces[intf_name]['status']
            result['device_protocol'] = device_interfaces[intf_name]['protocol']
        
        # Determine drift
        if in_netbox and in_device:
            # Both exist - compare enabled vs status
            netbox_should_be_up = result['netbox_enabled']
            device_is_up = 'up' in result['device_status'] and result['device_protocol'] == 'up'
            
            if netbox_should_be_up and not device_is_up:
                result['has_drift'] = True
                result['drift_reason'] = 'NetBox expects UP, but device is DOWN'
            elif not netbox_should_be_up and device_is_up:
                result['has_drift'] = True
                result['drift_reason'] = 'NetBox expects DOWN, but device is UP'
        elif in_netbox and not in_device:
            result['has_drift'] = True
            result['drift_reason'] = 'Interface exists in NetBox but not on device'
        elif not in_netbox and in_device:
            result['has_drift'] = True
            result['drift_reason'] = 'Interface exists on device but not in NetBox'
        
        comparison.append(result)
    
    return comparison
