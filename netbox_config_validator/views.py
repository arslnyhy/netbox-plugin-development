from django.shortcuts import render
from django.views import View
from django.db.models import Q
from dcim.models import Device
from .helpers import connect_to_device, get_device_interfaces, disconnect_device


class DriftCheckView(View):
    """
    View to check configuration drift between NetBox and devices.
    """
    
    def get(self, request):
        # Get all devices that have a primary IP configured (IPv4 or IPv6)
        devices = Device.objects.filter(
            Q(primary_ip4__isnull=False) | Q(primary_ip6__isnull=False)
        ).select_related(
            'primary_ip4',
            'primary_ip6',
            'platform',
            'site',
        ).order_by('name')
        
        # Collect device data with connection status and interfaces
        device_data = []
        for device in devices:
            device_ip = str(device.primary_ip4.address.ip) if device.primary_ip4 else None
            
            device_info = {
                'device': device,
                'connection_status': 'Not Attempted',
                'interfaces': {},
                'error': None,
            }
            
            if device_ip:
                # Try to connect and get interface data
                connection = connect_to_device(device_ip)
                
                if connection:
                    device_info['connection_status'] = 'Connected'
                    device_info['interfaces'] = get_device_interfaces(connection)
                    disconnect_device(connection)
                else:
                    device_info['connection_status'] = 'Failed'
                    device_info['error'] = 'Could not connect to device'
            else:
                device_info['error'] = 'No IPv4 address configured'
            
            device_data.append(device_info)
        
        context = {
            'device_data': device_data,
        }
        
        return render(request, 'netbox_config_validator/drift_check.html', context)

