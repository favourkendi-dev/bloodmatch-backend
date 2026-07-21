from django.contrib import admin
from .models import BloodRequest


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('blood_type', 'units_needed', 'urgency', 'city', 'status', 'hospital', 'created_at')
    list_filter = ('blood_type', 'urgency', 'status', 'city')
    search_fields = ('hospital__hospital_name', 'city', 'notes')
