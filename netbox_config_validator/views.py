from django.shortcuts import render, redirect
from django.views import View
from django.db.models import Q
from dcim.models import Device, Interface
from .helpers import connect_to_device, get_device_interfaces, disconnect_device, compare_interfaces
from datetime import datetime


class DriftCheckView(View):
    """
    View to check configuration drift between NetBox and devices.
    """
    
    def get(self, request):
        # Check if we have cached results in session
        cached_results = request.session.get('drift_check_results')
        check_time = request.session.get('drift_check_time')
        
        if cached_results:
            context = {
                'device_data': cached_results,
                'check_time': check_time,
            }
        else:
            # No cached results, show empty page
            context = {
                'device_data': None,
                'check_time': None,
            }
        
        return render(request, 'netbox_config_validator/drift_check.html', context)
    
    def post(self, request):
        # User clicked "Check Drift" - run the actual checks
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
                'device_name': device.name,
                'device_url': device.get_absolute_url(),
                'device_ip': device_ip,
                'platform': device.platform.name if device.platform else None,
                'site': device.site.name if device.site else None,
                'connection_status': 'Not Attempted',
                'drift_comparison': [],
                'error': None,
                'drift_count': 0,
            }
            
            if device_ip:
                # Try to connect and get interface data
                connection = connect_to_device(device_ip)
                
                if connection:
                    device_info['connection_status'] = 'Connected'
                    device_interfaces = get_device_interfaces(connection)
                    disconnect_device(connection)
                    
                    # Get NetBox interfaces and compare
                    netbox_interfaces = Interface.objects.filter(device=device)
                    device_info['drift_comparison'] = compare_interfaces(
                        netbox_interfaces,
                        device_interfaces
                    )
                    
                    # Count drifts
                    device_info['drift_count'] = sum(
                        1 for item in device_info['drift_comparison'] if item['has_drift']
                    )
                else:
                    device_info['connection_status'] = 'Failed'
                    device_info['error'] = 'Could not connect to device'
            else:
                device_info['error'] = 'No IPv4 address configured'
            
            device_data.append(device_info)
        
        # Store results in session
        request.session['drift_check_results'] = device_data
        request.session['drift_check_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Redirect to GET to avoid re-running on refresh
        return redirect('plugins:netbox_config_validator:drift_check')
