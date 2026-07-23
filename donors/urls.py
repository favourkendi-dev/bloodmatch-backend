from django.urls import path
from .views import MyDonorProfileView, MyDonationHistoryView, LeaderboardView, PublicDonorListView

urlpatterns = [
    path('', PublicDonorListView.as_view(), name='public_donor_list'),
    path('profile/', MyDonorProfileView.as_view(), name='my_donor_profile'),
    path('donations/', MyDonationHistoryView.as_view(), name='my_donation_history'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
