from django.urls import path
from .views import (
    MyHospitalProfileView,
    HospitalListView,
    AdminVerifyHospitalView,
    AdminUnverifyHospitalView,
)

urlpatterns = [
    path('profile/', MyHospitalProfileView.as_view(), name='my_hospital_profile'),
    path('', HospitalListView.as_view(), name='hospital_list'),
    path('admin/verify/<int:pk>/', AdminVerifyHospitalView.as_view(), name='admin_verify_hospital'),
    path('admin/unverify/<int:pk>/', AdminUnverifyHospitalView.as_view(), name='admin_unverify_hospital'),
]
