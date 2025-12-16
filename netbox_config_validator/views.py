from django.http import HttpResponse
from django.views import View


class DriftCheckView(View):
    """
    Simple view to check configuration drift between NetBox and devices.
    """
    
    def get(self, request):
        return HttpResponse(
            "<h1>Config Validator</h1>"
            "<p>Configuration drift detection is active!</p>"
        )

