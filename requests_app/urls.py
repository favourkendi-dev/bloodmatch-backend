from django.urls import path
from .views import (
    BloodRequestListCreateView,
    BloodRequestDetailView,
    MatchingDonorsView,
    SelectDonorView,
)

urlpatterns = [
    path('', BloodRequestListCreateView.as_view(), name='request_list_create'),
    path('<int:pk>/', BloodRequestDetailView.as_view(), name='request_detail'),
    path('<int:pk>/matches/', MatchingDonorsView.as_view(), name='request_matches'),
    path('<int:pk>/select_donor/', SelectDonorView.as_view(), name='request_select_donor'),
]
