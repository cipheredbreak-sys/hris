from django.contrib import admin
from .models import (
    Broker, BrokerUser, Employer, Carrier, Plan, 
    PlanPremium, EmployerOffering, CarrierCsvTemplate, ExportJob
)

@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ['agency_name', 'license_number', 'email', 'created_at']
    search_fields = ['agency_name', 'license_number', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(BrokerUser)
class BrokerUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'broker', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'broker']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ['name', 'broker', 'size', 'status', 'effective_date', 'created_at']
    list_filter = ['status', 'broker', 'size']
    search_fields = ['name', 'ein', 'contact_name', 'contact_email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'effective_date'

@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'carrier', 'plan_type', 'external_code', 'is_active']
    list_filter = ['plan_type', 'carrier', 'is_active']
    search_fields = ['name', 'external_code']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(PlanPremium)
class PlanPremiumAdmin(admin.ModelAdmin):
    list_display = ['plan', 'coverage_tier', 'monthly_premium', 'effective_date', 'end_date']
    list_filter = ['coverage_tier', 'plan__carrier', 'effective_date']
    search_fields = ['plan__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'effective_date'

@admin.register(EmployerOffering)
class EmployerOfferingAdmin(admin.ModelAdmin):
    list_display = ['employer', 'plan', 'contribution_mode', 'contribution_value', 'is_active']
    list_filter = ['contribution_mode', 'is_active', 'plan__plan_type']
    search_fields = ['employer__name', 'plan__name']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(CarrierCsvTemplate)
class CarrierCsvTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'carrier', 'coverage_type', 'is_active', 'created_at']
    list_filter = ['carrier', 'coverage_type', 'is_active']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = ['employer', 'carrier', 'coverage_type', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'carrier', 'coverage_type', 'created_at']
    search_fields = ['employer__name', 'file_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
