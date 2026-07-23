from django.urls import path
from .views import (
    BloodRequestListCreateView,
    BloodRequestDetailView,
    MatchingDonorsView,
    SelectDonorView,
    FulfillRequestView,
    CancelRequestView,
    AcceptDonorRequestView,
    DeclineDonorRequestView,
    MyMatchedRequestsView,
    VolunteerForRequestView,
    HospitalAnalyticsView,
)

urlpatterns = [
    path('analytics/', HospitalAnalyticsView.as_view(), name='hospital_analytics'),
    path('', BloodRequestListCreateView.as_view(), name='request_list_create'),
    path('my_matches/', MyMatchedRequestsView.as_view(), name='my_matched_requests'),
    path('<int:pk>/', BloodRequestDetailView.as_view(), name='request_detail'),
    path('<int:pk>/matches/', MatchingDonorsView.as_view(), name='request_matches'),
    path('<int:pk>/select_donor/', SelectDonorView.as_view(), name='request_select_donor'),
    path('<int:pk>/fulfill/', FulfillRequestView.as_view(), name='request_fulfill'),
    path('<int:pk>/cancel/', CancelRequestView.as_view(), name='request_cancel'),
    path('<int:pk>/accept/', AcceptDonorRequestView.as_view(), name='request_accept'),
    path('<int:pk>/decline/', DeclineDonorRequestView.as_view(), name='request_decline'),
    path('<int:pk>/volunteer/', VolunteerForRequestView.as_view(), name='request_volunteer'),
]
