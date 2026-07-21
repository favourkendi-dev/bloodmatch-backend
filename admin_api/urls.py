from django.urls import path
from .views import (
    AdminHospitalListView,
    VerifyHospitalView,
    AdminDonorListView,
    AdminRequestListView,
    AdminCancelRequestView,
    AdminReportsView,
)

urlpatterns = [
    path('hospitals/', AdminHospitalListView.as_view(), name='admin_hospital_list'),
    path('hospitals/<int:pk>/verify/', VerifyHospitalView.as_view(), name='admin_verify_hospital'),
    path('donors/', AdminDonorListView.as_view(), name='admin_donor_list'),
    path('requests/', AdminRequestListView.as_view(), name='admin_request_list'),
    path('requests/<int:pk>/cancel/', AdminCancelRequestView.as_view(), name='admin_cancel_request'),
    path('reports/', AdminReportsView.as_view(), name='admin_reports'),
]
