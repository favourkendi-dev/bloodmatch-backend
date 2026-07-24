from django.db.models import Count
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from donors.models import DonorProfile, Donation
from hospitals.models import HospitalProfile
from requests_app.models import BloodRequest


@api_view(['GET'])
@permission_classes([AllowAny])
def public_stats(request):
    total_donors = DonorProfile.objects.count()
    total_hospitals = HospitalProfile.objects.count()
    verified_hospitals = HospitalProfile.objects.filter(is_verified=True).count()

    completed_donations = Donation.objects.filter(status=Donation.Status.COMPLETED)
    total_donations = completed_donations.count()
    total_units_donated = sum(d.units_donated for d in completed_donations)

    fulfilled_requests = BloodRequest.objects.filter(status='fulfilled').count()

    blood_type_breakdown = dict(
        DonorProfile.objects.exclude(blood_type='')
        .values_list('blood_type')
        .annotate(count=Count('id'))
        .values_list('blood_type', 'count')
    )

    return Response({
        'total_donors': total_donors,
        'total_hospitals': total_hospitals,
        'verified_hospitals': verified_hospitals,
        'total_donations': total_donations,
        'total_units_donated': total_units_donated,
        'fulfilled_requests': fulfilled_requests,
        'blood_type_breakdown': blood_type_breakdown,
    })
