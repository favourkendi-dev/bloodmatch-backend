from django.contrib import admin
from .models import HospitalProfile


@admin.register(HospitalProfile)
class HospitalProfileAdmin(admin.ModelAdmin):
    list_display = ('hospital_name', 'user', 'city', 'contact_phone')
    list_filter = ('city',)
    search_fields = ('hospital_name', 'user__username', 'user__email', 'city')
