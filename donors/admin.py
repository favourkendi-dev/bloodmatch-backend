from django.contrib import admin
from .models import DonorProfile


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_type', 'city', 'is_available', 'last_donation_date')
    list_filter = ('blood_type', 'is_available', 'city')
    search_fields = ('user__username', 'user__email', 'city')
