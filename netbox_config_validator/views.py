from django.shortcuts import render
from django.views import View
from django.db.models import Q
from dcim.models import Device


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
        
        context = {
            'devices': devices,
        }
        
        return render(request, 'netbox_config_validator/drift_check.html', context)

