from django.urls import path
from .views import BloodRequestListCreateView, BloodRequestDetailView

urlpatterns = [
    path('', BloodRequestListCreateView.as_view(), name='request_list_create'),
    path('<int:pk>/', BloodRequestDetailView.as_view(), name='request_detail'),
]
