from django.urls import path
from .views import MyHospitalProfileView

urlpatterns = [
    path('profile/', MyHospitalProfileView.as_view(), name='my_hospital_profile'),
]
