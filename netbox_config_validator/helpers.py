"""
Helper functions for device connection and data collection.
"""
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import re


def connect_to_device(device_ip, username='admin', password='letmein', device_type='cisco_ios'):
    """
    Connect to a network device using Netmiko.
    
    Args:
        device_ip: IP address of the device
        username: SSH username
        password: SSH password
        device_type: Netmiko device type (default: cisco_ios)
    
    Returns:
        Netmiko connection object or None if connection fails
    """
    try:
        device_params = {
            'device_type': device_type,
            'host': device_ip,
            'username': username,
            'password': password,
            'timeout': 10,
            'session_log': None,
        }
        
        connection = ConnectHandler(**device_params)
        return connection
        
    except NetmikoTimeoutException:
        return None
    except NetmikoAuthenticationException:
        return None
    except Exception as e:
        return None


def get_device_interfaces(connection):
    """
    Get interface status from device using 'show ip interface brief'.
    
    Args:
        connection: Active Netmiko connection
    
    Returns:
        Dictionary with interface names as keys and status info as values
        Example: {'GigabitEthernet0/0': {'status': 'up', 'protocol': 'up', 'ip': '10.1.1.1'}}
    """
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
        
    except Exception as e:
        return {}


def disconnect_device(connection):
    """
    Safely disconnect from device.
    
    Args:
        connection: Active Netmiko connection
    """
    if connection:
        try:
            connection.disconnect()
        except:
            pass

