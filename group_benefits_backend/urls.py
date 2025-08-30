"""
URL configuration for group_benefits_backend project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from accounts.views import dashboard_view, employers_view, employees_view, benefits_view, reports_view, exports_view, onboarding_wizard_view, bulk_import_employees, download_employee_template, create_plan_templates, carrier_setup_view, system_config_view, employee_form_view, employer_forms_view, broker_dashboard_view, employee_portal_login_view, employee_portal_dashboard_view

# Swagger/OpenAPI schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="HRIS Group Benefits API",
        default_version='v1',
        description="""
        **HRIS Group Benefits Management System API**
        
        A comprehensive API for managing group benefits enrollment, user authentication, and broker console operations.
        
        ## 🚀 Development Mode Active
        **Authentication is DISABLED for easier testing!**
        
        All API endpoints are accessible without authentication. You can:
        - Test any endpoint directly without tokens
        - Skip the "Authorize" button below
        - Use endpoints freely in Swagger UI
        
        ## Authentication (Optional in Dev Mode)
        This API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:
        ```
        Authorization: Bearer <your_jwt_token>
        ```
        
        ## Key Features
        - **Multi-tenant RBAC**: Role-based access control for brokers, employers, carriers, and employees
        - **Social Authentication**: Google and Microsoft OAuth integration
        - **Employee Management**: Comprehensive employee and dependent management
        - **Benefits Enrollment**: Complete enrollment workflow with plan comparisons
        - **Reporting**: Detailed analytics and export capabilities
        
        ## 🚀 Quick Start - Copy & Paste Test Tokens
        **Click "Authorize" button and paste one of these ready-to-use tokens:**
        
        **🔑 SUPER ADMIN (Full Access):**
        ```
        Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU4ODg0NTE5LCJpYXQiOjE3NTYyOTI1MTksImp0aSI6ImEwYTkwZWViMGY2NzRkZmJhMmQxYWQxYTRkZWJjMGRlIiwidXNlcl9pZCI6IjIifQ._op2DR09L63_rbJauoYO64J-PVnqQ9miwHlOvRtrti8
        ```
        
        **👤 EMPLOYEE (Limited Access):**
        ```
        Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU4ODg0NTI1LCJpYXQiOjE3NTYyOTI1MjUsImp0aSI6IjRjNTJjNGI3M2RhMjQ3YmQ4ZWNiMmQ1YmZkZjBhNzhmIiwidXNlcl9pZCI6IjgifQ.3SLoSfFMOOAYeCKoq6ddjSMmCE8G6PEYeUX9g41bcvI
        ```
        
        ## Test Account Credentials (Alternative Login Method)
        - **Super Admin**: `superadmin@test.com` / `SuperAdmin123!`
        - **Broker Admin**: `brokeradmin@test.com` / `BrokerAdmin123!`
        - **Employer Admin**: `employeradmin@test.com` / `EmployerAdmin123!`
        - **Employee**: `employee@test.com` / `Employee123!`
        """,
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="support@hrisbenefit.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

def api_root(request):
    """API root endpoint with basic information and links"""
    from django.conf import settings
    
    response_data = {
        "message": "Welcome to HRIS Group Benefits API",
        "version": "1.0.0",
        "documentation": {
            "swagger_ui": request.build_absolute_uri('/swagger/'),
            "redoc": request.build_absolute_uri('/redoc/'),
            "openapi_schema": request.build_absolute_uri('/swagger.json'),
        },
        "endpoints": {
            "authentication": request.build_absolute_uri('/api/auth/'),
            "users": request.build_absolute_uri('/api/users/'),
            "organizations": request.build_absolute_uri('/api/organizations/'),
            "employees": request.build_absolute_uri('/api/employees/'),
            "admin": request.build_absolute_uri('/admin/'),
        }
    }
    
    # Add development mode info
    if getattr(settings, 'DEV_MODE', False):
        response_data["development_mode"] = {
            "enabled": True,
            "authentication_required": False,
            "message": "🚀 Development Mode: All API endpoints accessible without authentication!",
            "note": "Set DEV_MODE=False in production"
        }
        response_data["test_credentials"] = {
            "super_admin": {"email": "superadmin@test.com", "password": "SuperAdmin123!"},
            "broker_admin": {"email": "brokeradmin@test.com", "password": "BrokerAdmin123!"},
            "employer_admin": {"email": "employeradmin@test.com", "password": "EmployerAdmin123!"},
            "employee": {"email": "employee@test.com", "password": "Employee123!"},
            "note": "Authentication is optional in development mode"
        }
    else:
        response_data["authentication_required"] = True
    
    return JsonResponse(response_data)

urlpatterns = [
    # Root API endpoint
    path('', api_root, name='api-root'),
    
    # Dashboard and Navigation
    path('dashboard/', dashboard_view, name='dashboard'),
    path('employers/', employers_view, name='employers'),
    path('employees/', employees_view, name='employees'),
    path('benefits/', benefits_view, name='benefits'),
    path('reports/', reports_view, name='reports'),
    path('exports/', exports_view, name='exports'),
    path('onboarding/', onboarding_wizard_view, name='onboarding_wizard'),
    path('carrier-setup/', carrier_setup_view, name='carrier_setup'),
    path('system-config/', system_config_view, name='system_config'),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-docs'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Django Allauth URLs (for social auth and account management)
    path('accounts/', include('allauth.urls')),
    
    # API endpoints
    path('api/', include('accounts.urls')),  # Authentication and user management APIs
    path('api/', include('broker_console.urls')),  # Existing broker console APIs
    
    # Bulk import endpoints
    path('api/bulk-import/employees/', bulk_import_employees, name='bulk_import_employees'),
    path('api/download/employee-template/', download_employee_template, name='download_employee_template'),
    path('api/create/plan-templates/', create_plan_templates, name='create_plan_templates'),
    
    # Employee form and employer review
    path('employee-form/<uuid:employer_id>/', employee_form_view, name='employee_form'),
    path('employer-forms/<uuid:employer_id>/', employer_forms_view, name='employer_forms'),
    path('broker-dashboard/', broker_dashboard_view, name='broker_dashboard'),
    
    # Employee Portal
    path('employee-portal/login/', employee_portal_login_view, name='employee_portal_login'),
    path('employee-portal/dashboard/', employee_portal_dashboard_view, name='employee_portal_dashboard'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
