from django.urls import path
from . import views

urlpatterns = [
    path('', views.DriftCheckView.as_view(), name='drift_check'),
]

