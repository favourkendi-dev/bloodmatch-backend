from django.urls import path
from .views import MyDonorProfileView

urlpatterns = [
    path('profile/', MyDonorProfileView.as_view(), name='my_donor_profile'),
]
