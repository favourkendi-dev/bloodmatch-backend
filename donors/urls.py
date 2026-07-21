from django.urls import path
from .views import MyDonorProfileView, MyDonationHistoryView

urlpatterns = [
    path('profile/', MyDonorProfileView.as_view(), name='my_donor_profile'),
    path('donations/', MyDonationHistoryView.as_view(), name='my_donation_history'),
]
