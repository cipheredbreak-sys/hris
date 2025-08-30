from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group, Permission
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Organization, Membership, AuditEvent, UserProfile
import json

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that returns user data along with tokens"""
    
    @swagger_auto_schema(
        operation_description="Login with email and password",
        operation_summary="User Login",
        tags=['Authentication'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: 'Login successful'}
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Get user from email
            email = request.data.get('email')
            try:
                user = User.objects.get(email=email)
                response.data['user'] = {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_superuser': user.is_superuser,
                }
                
                # Add user's organizations and roles
                memberships = Membership.objects.filter(user=user).select_related('organization')
                response.data['organizations'] = [
                    {
                        'id': m.organization.id,
                        'name': m.organization.name,
                        'role': m.role,
                    } for m in memberships
                ]
                
            except User.DoesNotExist:
                pass
        
        return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Logout view that blacklists the refresh token"""
    try:
        refresh_token = request.data.get("refresh_token")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """Get current user information"""
    user = request.user
    
    # Get user's organizations and roles
    memberships = Membership.objects.filter(user=user).select_related('organization')
    organizations = [
        {
            'id': m.organization.id,
            'name': m.organization.name,
            'slug': m.organization.slug,
            'role': m.role,
        } for m in memberships
    ]
    
    return Response({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_superuser': user.is_superuser,
        'organizations': organizations,
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Change user password"""
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not user.check_password(old_password):
        return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    user.save()
    
    # Create audit event
    AuditEvent.objects.create(
        user=user,
        event='password_change',
        metadata={'method': 'api'}
    )
    
    return Response({"message": "Password changed successfully"})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def social_auth(request):
    """Social authentication demo handler"""
    provider = request.data.get('provider', '')
    
    if provider in ['google', 'microsoft']:
        # For development/demo purposes, create a demo user
        demo_email = f"demo.user@{provider}.com"
        
        try:
            user = User.objects.get(email=demo_email)
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=demo_email,
                first_name=f"Demo",
                last_name=f"User ({provider.title()})",
                password=None  # No password for social users
            )
            
            # Create audit event
            AuditEvent.objects.create(
                user=user,
                event='social_account_added',
                metadata={'provider': provider, 'method': 'demo'}
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'provider': provider,
            'demo': True
        })
    
    return Response({
        "error": "Invalid provider",
        "available_providers": ["google", "microsoft"]
    }, status=status.HTTP_400_BAD_REQUEST)


class UserListCreateView(generics.ListCreateAPIView):
    """List and create users"""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers import UserListSerializer
        return UserListSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a user"""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers import UserDetailSerializer
        return UserDetailSerializer


class OrganizationListCreateView(generics.ListCreateAPIView):
    """List and create organizations"""
    queryset = Organization.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers import OrganizationListSerializer
        return OrganizationListSerializer


class OrganizationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an organization"""
    queryset = Organization.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers import OrganizationDetailSerializer
        return OrganizationDetailSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_permissions(request, user_id):
    """Get user permissions"""
    try:
        user = User.objects.get(id=user_id)
        permissions_list = user.get_all_permissions()
        return Response({
            'user_id': user_id,
            'permissions': list(permissions_list)
        })
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class GroupListCreateView(generics.ListCreateAPIView):
    """List and create groups (roles)"""
    queryset = Group.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers import GroupListSerializer
        return GroupListSerializer


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a group"""
    queryset = Group.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers import GroupDetailSerializer
        return GroupDetailSerializer


class PermissionListView(generics.ListAPIView):
    """List all permissions"""
    queryset = Permission.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers import PermissionSerializer
        return PermissionSerializer


class RolePermissionMatrixListCreateView(generics.ListCreateAPIView):
    """List and create role permission matrix (legacy)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Return empty queryset since we're using new RBAC system
        return []
    
    def list(self, request):
        return Response({
            "message": "Legacy role permission matrix. Use new RBAC system via Django Groups.",
            "groups": [group.name for group in Group.objects.all()]
        })


class AuditLogListView(generics.ListAPIView):
    """List audit events"""
    queryset = AuditEvent.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from .serializers import AuditEventSerializer
        return AuditEventSerializer


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from broker_console.models import Employer, Employee, Plan, Carrier, EmployeeFormSubmission

@login_required
def dashboard_view(request):
    """Dashboard view for authenticated users"""
    # Get dashboard statistics
    stats = {
        'users_count': User.objects.count(),
        'organizations_count': Organization.objects.count(),
        'memberships_count': Membership.objects.count(),
        'audit_events_count': AuditEvent.objects.count(),
        'recent_events': []
    }
    
    # Get recent audit events
    recent_events = AuditEvent.objects.select_related('user', 'organization').order_by('-created_at')[:5]
    stats['recent_events'] = recent_events
    
    return render(request, 'dashboard/index.html', {
        'stats': stats
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    stats = {
        'users_count': User.objects.count(),
        'organizations_count': Organization.objects.count(),
        'memberships_count': Membership.objects.count(),
        'audit_events_count': AuditEvent.objects.count(),
        'recent_events': []
    }
    
    # Get recent audit events
    recent_events = AuditEvent.objects.select_related('user', 'organization').order_by('-created_at')[:10]
    stats['recent_events'] = [
        {
            'event': event.event,
            'user': event.user.email if event.user else 'Anonymous',
            'created_at': event.created_at,
            'organization': event.organization.name if event.organization else None
        } for event in recent_events
    ]
    
    return Response(stats)

# Dashboard Navigation Views

@login_required
def employers_view(request):
    """Employers list view for Broker Admin"""
    if not (request.user.is_superuser or request.user.groups.filter(name='Broker Admin').exists()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from broker_console.models import Employer, Employee
    
    # Get employers (with search/filter functionality)
    employers = Employer.objects.all().annotate(
        employee_count=Count('employees')
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        employers = employers.filter(
            Q(name__icontains=search_query) | 
            Q(ein__icontains=search_query) |
            Q(contact_name__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        employers = employers.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(employers, 20)
    page_number = request.GET.get('page')
    employers_page = paginator.get_page(page_number)
    
    # Stats for dashboard cards
    stats = {
        'total_employers': Employer.objects.count(),
        'active_employers': Employer.objects.filter(status='active').count(),
        'total_employees': Employee.objects.count(),
        'pending_renewals': 3  # Mock data for now
    }
    
    return render(request, 'dashboard/employers.html', {
        'employers': employers_page,
        'stats': stats,
        'search_query': search_query,
        'status_filter': status_filter,
    })

@login_required
def employees_view(request):
    """Employees list view"""
    # Check permissions
    if not (request.user.is_superuser or 
            request.user.groups.filter(name__in=['Broker Admin', 'Employer Admin']).exists()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    from broker_console.models import Employee, Employer
    from datetime import date, timedelta
    
    # Get employees based on user role
    if request.user.is_superuser or request.user.groups.filter(name='Broker Admin').exists():
        # Broker can see all employees
        employees = Employee.objects.select_related('employer').order_by('-created_at')
    else:
        # Employer Admin sees only their employees
        user_memberships = request.user.memberships.all()
        employer_orgs = [m.organization for m in user_memberships]
        # For now, show all employees - would need better org-to-employer mapping
        employees = Employee.objects.select_related('employer').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        employees = employees.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        employees = employees.filter(employment_status=status_filter)
    
    # Employer filter
    employer_filter = request.GET.get('employer', '')
    if employer_filter:
        employees = employees.filter(employer_id=employer_filter)
    
    # Pagination
    paginator = Paginator(employees, 20)
    page_number = request.GET.get('page')
    employees_page = paginator.get_page(page_number)
    
    # Get employers for filter dropdown
    employers = Employer.objects.filter(status='active').order_by('name')
    
    # Stats
    recent_date = date.today() - timedelta(days=90)
    stats = {
        'total_employees': employees.count(),
        'active_employees': employees.filter(employment_status='active').count(),
        'pending_enrollments': 5,  # Mock data
        'recent_hires': employees.filter(hire_date__gte=recent_date).count()
    }
    
    return render(request, 'dashboard/employees.html', {
        'employees': employees_page,
        'stats': stats,
        'search_query': search_query,
        'status_filter': status_filter,
        'employer_filter': employer_filter,
        'employers': employers,
    })

@login_required 
def benefits_view(request):
    """Benefits/Plans view"""
    from broker_console.models import Plan, Carrier
    
    # Get available plans
    plans = Plan.objects.select_related('carrier').filter(is_active=True).order_by('plan_type', 'name')
    carriers = Carrier.objects.filter(is_active=True).order_by('name')
    
    # Filter by plan type
    plan_type_filter = request.GET.get('plan_type', '')
    if plan_type_filter:
        plans = plans.filter(plan_type=plan_type_filter)
    
    # Filter by carrier
    carrier_filter = request.GET.get('carrier', '')
    if carrier_filter:
        plans = plans.filter(carrier_id=carrier_filter)
    
    # Pagination
    paginator = Paginator(plans, 20)
    page_number = request.GET.get('page')
    plans_page = paginator.get_page(page_number)
    
    # Stats
    stats = {
        'total_plans': Plan.objects.filter(is_active=True).count(),
        'medical_plans': Plan.objects.filter(plan_type='medical', is_active=True).count(),
        'dental_plans': Plan.objects.filter(plan_type='dental', is_active=True).count(),
        'vision_plans': Plan.objects.filter(plan_type='vision', is_active=True).count(),
    }
    
    return render(request, 'dashboard/benefits.html', {
        'plans': plans_page,
        'carriers': carriers,
        'stats': stats,
        'plan_type_filter': plan_type_filter,
        'carrier_filter': carrier_filter,
    })

@login_required
def reports_view(request):
    """Reports view"""
    if not (request.user.is_superuser or 
            request.user.groups.filter(name__in=['Broker Admin', 'Employer Admin']).exists()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Mock report data for now
    reports = [
        {
            'name': 'Monthly Enrollment Report',
            'description': 'Summary of employee enrollments for the current month',
            'type': 'enrollment',
            'last_generated': '2025-08-27',
        },
        {
            'name': 'Premium Summary',
            'description': 'Total premiums and contribution breakdown',
            'type': 'financial',
            'last_generated': '2025-08-25',
        },
        {
            'name': 'Employee Census',
            'description': 'Complete employee demographic and enrollment data',
            'type': 'census',
            'last_generated': '2025-08-20',
        },
    ]
    
    return render(request, 'dashboard/reports.html', {
        'reports': reports,
    })

@login_required
def exports_view(request):
    """Exports view"""
    if not (request.user.is_superuser or 
            request.user.groups.filter(name__in=['Broker Admin', 'Employer Admin']).exists()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get recent export jobs (from the model)
    from broker_console.models import ExportJob
    exports = ExportJob.objects.select_related('employer', 'carrier').order_by('-created_at')[:20]
    
    return render(request, 'dashboard/exports.html', {
        'exports': exports,
    })

@login_required
def onboarding_wizard_view(request):
    """Company onboarding wizard for brokers"""
    if not (request.user.is_superuser or request.user.groups.filter(name='Broker Admin').exists()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    return render(request, 'dashboard/onboarding_wizard.html')

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def bulk_import_employees(request):
    """Handle bulk employee import from CSV/Excel files"""
    # Skip permission check in development mode
    # if not (request.user.is_superuser or request.user.groups.filter(name='Broker Admin').exists()):
    #     return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    uploaded_file = request.FILES['file']
    employer_id = request.data.get('employer_id')
    
    if not employer_id:
        return Response({'error': 'Employer ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from broker_console.models import Employer, Employee
        employer = Employer.objects.get(id=employer_id)
        
        # Process the file
        import pandas as pd
        import io
        
        # Read file based on extension
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(io.StringIO(uploaded_file.read().decode('utf-8')))
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            return Response({'error': 'Unsupported file format. Please use CSV or Excel.'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Validate required columns - support both detailed and simplified formats
        # Simplified format: name, date_of_birth, status
        # Detailed format: first_name, last_name, email, employee_id
        
        has_simplified_format = 'name' in df.columns and 'date_of_birth' in df.columns and 'status' in df.columns
        has_detailed_format = all(col in df.columns for col in ['first_name', 'last_name', 'email', 'employee_id'])
        
        if not (has_simplified_format or has_detailed_format):
            return Response({
                'error': 'File must contain either simplified format (name, date_of_birth, status) or detailed format (first_name, last_name, email, employee_id)',
                'simplified_format': ['name', 'date_of_birth', 'status'],
                'detailed_format': ['first_name', 'last_name', 'email', 'employee_id']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process employees
        created_employees = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                if has_simplified_format:
                    # Handle simplified format (name, date_of_birth, status)
                    full_name = str(row['name']).strip()
                    name_parts = full_name.split(' ', 1)
                    first_name = name_parts[0] if name_parts else 'Unknown'
                    last_name = name_parts[1] if len(name_parts) > 1 else 'Employee'
                    
                    # Generate a unique employee ID
                    import time
                    employee_id = f"EMP{int(time.time())}{index:03d}"
                    email = f"{first_name.lower()}.{last_name.lower()}@company.com"
                    
                    # Parse status to hours_per_week
                    status_str = str(row['status']).strip().upper()
                    hours_per_week = 40.0 if status_str == 'FT' else 20.0 if status_str == 'PT' else 40.0
                    
                    # Check if employee already exists by name and date of birth
                    existing = Employee.objects.filter(
                        first_name=first_name, 
                        last_name=last_name, 
                        date_of_birth=pd.to_datetime(row['date_of_birth']).date(),
                        employer=employer
                    ).exists()
                    
                    if existing:
                        errors.append(f"Row {index + 2}: Employee {full_name} with this birth date already exists")
                        continue
                    
                    employee_data = {
                        'employer': employer,
                        'employee_id': employee_id,
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': row.get('email', email),
                        'date_of_birth': pd.to_datetime(row['date_of_birth']).date(),
                        'hours_per_week': hours_per_week,
                        'hire_date': pd.to_datetime(row.get('hire_date', None)).date() if pd.notna(row.get('hire_date')) else pd.Timestamp.now().date(),
                        'department': row.get('department', ''),
                        'salary': float(row.get('salary', 50000)),
                        'employment_status': 'active',
                        'ssn': '000-00-0000',  # Default placeholder
                        'gender': 'M',  # Default
                        'address_line1': row.get('address', '123 Main St'),
                        'city': row.get('city', 'City'),
                        'state': row.get('state', 'ST'),
                        'zip_code': row.get('zip_code', '12345'),
                        'phone': row.get('phone', ''),
                    }
                else:
                    # Handle detailed format (existing logic)
                    # Check if employee already exists
                    if Employee.objects.filter(employee_id=row['employee_id'], employer=employer).exists():
                        errors.append(f"Row {index + 2}: Employee {row['employee_id']} already exists")
                        continue
                    
                    employee_data = {
                        'employer': employer,
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'email': row['email'],
                        'employee_id': row['employee_id'],
                        'hire_date': pd.to_datetime(row.get('hire_date', None)).date() if pd.notna(row.get('hire_date')) else pd.Timestamp.now().date(),
                        'department': row.get('department', ''),
                        'salary': float(row['salary']) if pd.notna(row.get('salary')) else 50000.0,
                        'employment_status': row.get('employment_status', 'active'),
                        'date_of_birth': pd.to_datetime(row.get('date_of_birth', None)).date() if pd.notna(row.get('date_of_birth')) else None,
                        'ssn': row.get('ssn', '000-00-0000'),
                        'gender': row.get('gender', 'M'),
                        'address_line1': row.get('address', '123 Main St'),
                        'city': row.get('city', 'City'),
                        'state': row.get('state', 'ST'),
                        'zip_code': row.get('zip_code', '12345'),
                        'phone': row.get('phone', ''),
                        'hours_per_week': float(row.get('hours_per_week', 40.0)),
                    }
                
                employee = Employee.objects.create(**employee_data)
                created_employees.append({
                    'id': employee.id,
                    'name': f"{employee.first_name} {employee.last_name}",
                    'employee_id': employee.employee_id
                })
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
        
        # Create audit event
        if request.user.is_authenticated:
            AuditEvent.objects.create(
                user=request.user,
                event='bulk_employee_import',
                metadata={
                    'employer_id': employer_id,
                    'total_rows': len(df),
                    'created_count': len(created_employees),
                    'error_count': len(errors)
                }
            )
        
        return Response({
            'success': True,
            'message': f'Successfully imported {len(created_employees)} employees',
            'created_employees': created_employees,
            'errors': errors,
            'total_processed': len(df),
            'total_created': len(created_employees),
            'total_errors': len(errors)
        })
        
    except Employer.DoesNotExist:
        return Response({'error': 'Employer not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Import failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_employee_template(request):
    """Download employee import template"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employee_template.csv"'
    
    writer = csv.writer(response)
    headers = [
        'first_name', 'last_name', 'email', 'employee_id', 'hire_date', 
        'department', 'salary', 'employment_status', 'birth_date', 'address',
        'phone', 'emergency_contact_name', 'emergency_contact_phone'
    ]
    
    writer.writerow(headers)
    
    # Add sample data
    writer.writerow([
        'John', 'Doe', 'john.doe@company.com', 'EMP001', '2025-01-15',
        'Engineering', '75000', 'active', '1985-03-20', '123 Main St, City, ST 12345',
        '555-123-4567', 'Jane Doe', '555-987-6543'
    ])
    
    return response

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_plan_templates(request):
    """Create standard plan templates for a new employer"""
    if not (request.user.is_superuser or request.user.groups.filter(name='Broker Admin').exists()):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    employer_id = request.data.get('employer_id')
    selected_plans = request.data.get('selected_plans', [])
    
    if not employer_id:
        return Response({'error': 'Employer ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from broker_console.models import Employer, Plan, Carrier
        employer = Employer.objects.get(id=employer_id)
        
        # Get or create default carriers
        aetna, _ = Carrier.objects.get_or_create(
            name='Aetna',
            defaults={'code': 'AETNA', 'is_active': True}
        )
        anthem, _ = Carrier.objects.get_or_create(
            name='Anthem',
            defaults={'code': 'ANTHEM', 'is_active': True}
        )
        
        created_plans = []
        
        # Plan templates based on selections
        plan_templates = {
            'medical_hmo': {
                'name': 'HMO Select',
                'plan_type': 'medical',
                'carrier': aetna,
                'network_type': 'HMO',
                'description': 'Comprehensive HMO plan with local network focus',
                'employee_premium': 150.00,
                'family_premium': 450.00,
                'individual_deductible': 1500.00,
                'family_deductible': 3000.00,
                'individual_oop_max': 6000.00,
                'family_oop_max': 12000.00,
                'copay_primary': 25.00,
                'copay_specialist': 50.00,
                'copay_er': 150.00,
                'is_active': True
            },
            'medical_ppo': {
                'name': 'PPO Plus',
                'plan_type': 'medical',
                'carrier': anthem,
                'network_type': 'PPO',
                'description': 'Flexible PPO plan with nationwide network',
                'employee_premium': 200.00,
                'family_premium': 600.00,
                'individual_deductible': 1000.00,
                'family_deductible': 2000.00,
                'individual_oop_max': 5000.00,
                'family_oop_max': 10000.00,
                'copay_primary': 20.00,
                'copay_specialist': 40.00,
                'copay_er': 100.00,
                'is_active': True
            },
            'medical_hdhp': {
                'name': 'HDHP + HSA',
                'plan_type': 'medical',
                'carrier': aetna,
                'network_type': 'HDHP',
                'description': 'High deductible health plan with HSA eligibility',
                'employee_premium': 100.00,
                'family_premium': 300.00,
                'individual_deductible': 2500.00,
                'family_deductible': 5000.00,
                'individual_oop_max': 7000.00,
                'family_oop_max': 14000.00,
                'hsa_employer_contribution': 1000.00,
                'is_active': True
            },
            'dental_basic': {
                'name': 'Basic Dental',
                'plan_type': 'dental',
                'carrier': aetna,
                'description': 'Preventive and basic dental coverage',
                'employee_premium': 25.00,
                'family_premium': 75.00,
                'annual_max': 1000.00,
                'preventive_coverage': 100,  # 100%
                'basic_coverage': 80,        # 80%
                'major_coverage': 50,        # 50%
                'is_active': True
            },
            'dental_enhanced': {
                'name': 'Enhanced Dental',
                'plan_type': 'dental',
                'carrier': anthem,
                'description': 'Comprehensive dental with orthodontia',
                'employee_premium': 40.00,
                'family_premium': 120.00,
                'annual_max': 2000.00,
                'preventive_coverage': 100,  # 100%
                'basic_coverage': 80,        # 80%
                'major_coverage': 60,        # 60%
                'orthodontia_coverage': 50,  # 50%
                'orthodontia_max': 2000.00,
                'is_active': True
            },
            'vision_standard': {
                'name': 'Standard Vision',
                'plan_type': 'vision',
                'carrier': aetna,
                'description': 'Annual eye exams and eyewear allowance',
                'employee_premium': 8.00,
                'family_premium': 20.00,
                'copay_exam': 10.00,
                'frame_allowance': 150.00,
                'lens_allowance': 150.00,
                'contact_allowance': 150.00,
                'is_active': True
            },
            'life_basic': {
                'name': 'Basic Life Insurance',
                'plan_type': 'life',
                'carrier': aetna,
                'description': 'Employer-paid basic life insurance',
                'coverage_amount': '1x Annual Salary',
                'max_coverage': 50000.00,
                'employee_premium': 0.00,  # Employer paid
                'is_active': True
            },
            'life_supplemental': {
                'name': 'Supplemental Life',
                'plan_type': 'life',
                'carrier': aetna,
                'description': 'Optional additional life insurance',
                'coverage_options': '1x, 2x, 3x, 4x, 5x Annual Salary',
                'max_coverage': 500000.00,
                'rate_per_1000': 0.50,
                'is_active': True
            },
            'disability_std': {
                'name': 'Short-Term Disability',
                'plan_type': 'disability',
                'carrier': aetna,
                'description': 'Short-term disability income protection',
                'benefit_percentage': 60,
                'max_weekly_benefit': 1500.00,
                'elimination_period': 7,  # days
                'max_benefit_period': 26,  # weeks
                'employee_premium': 0.00,  # Employer paid
                'is_active': True
            },
            'disability_ltd': {
                'name': 'Long-Term Disability',
                'plan_type': 'disability',
                'carrier': aetna,
                'description': 'Long-term disability income protection',
                'benefit_percentage': 60,
                'max_monthly_benefit': 5000.00,
                'elimination_period': 90,  # days
                'benefit_to_age': 65,
                'employee_premium': 0.00,  # Employer paid
                'is_active': True
            }
        }
        
        # Create selected plans
        for plan_key in selected_plans:
            if plan_key in plan_templates:
                template = plan_templates[plan_key]
                plan = Plan.objects.create(**template)
                
                # Create employer offering for this plan
                from broker_console.models import EmployerOffering
                EmployerOffering.objects.create(
                    employer=employer,
                    plan=plan,
                    is_active=True,
                    employer_contribution_percent=75.0  # Default 75% contribution
                )
                
                created_plans.append({
                    'id': plan.id,
                    'name': plan.name,
                    'type': plan.plan_type,
                    'carrier': plan.carrier.name
                })
        
        # Create audit event
        AuditEvent.objects.create(
            user=request.user,
            event='plan_templates_created',
            metadata={
                'employer_id': employer_id,
                'plans_created': len(created_plans),
                'selected_plans': selected_plans
            }
        )
        
        return Response({
            'success': True,
            'message': f'Successfully created {len(created_plans)} plan templates',
            'created_plans': created_plans
        })
        
    except Employer.DoesNotExist:
        return Response({'error': 'Employer not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Plan creation failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def carrier_setup_view(request):
    """Carrier integration setup for brokers"""
    if not (request.user.is_superuser or request.user.groups.filter(name='Broker Admin').exists()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get carrier statistics
    from broker_console.models import Carrier
    stats = {
        'total_carriers': Carrier.objects.count(),
        'active_carriers': Carrier.objects.filter(is_active=True).count(),
        'integrated_carriers': Carrier.objects.filter(is_active=True).count(),  # Simplified for demo
        'pending_connections': 1  # Mock data
    }
    
    return render(request, 'dashboard/carrier_setup.html', {'stats': stats})

@login_required
def system_config_view(request):
    """System configuration for superusers and broker admins"""
    if not (request.user.is_superuser or request.user.groups.filter(name='Broker Admin').exists()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    return render(request, 'dashboard/system_config.html')

def employee_form_view(request, employer_id):
    """Employee form submission page"""
    try:
        employer = Employer.objects.get(id=employer_id)
    except Employer.DoesNotExist:
        messages.error(request, 'Employer not found.')
        return redirect('dashboard')
    
    return render(request, 'employee_form.html', {
        'employer': employer
    })

@login_required  
def employer_forms_view(request, employer_id):
    """Employer dashboard for reviewing form submissions"""
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Broker Admin', 'Employer Admin']).exists()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    try:
        employer = Employer.objects.get(id=employer_id)
    except Employer.DoesNotExist:
        messages.error(request, 'Employer not found.')
        return redirect('employers')
    
    # Get form submissions for this employer
    submissions = EmployeeFormSubmission.objects.filter(employer=employer).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        submissions = submissions.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        submissions = submissions.filter(status=status_filter)
    
    # Date filter
    date_filter = request.GET.get('date', '')
    if date_filter:
        from datetime import date, timedelta
        today = date.today()
        if date_filter == 'today':
            submissions = submissions.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = today - timedelta(days=7)
            submissions = submissions.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - timedelta(days=30)
            submissions = submissions.filter(created_at__date__gte=month_ago)
    
    # Pagination
    paginator = Paginator(submissions, 20)
    page_number = request.GET.get('page')
    submissions_page = paginator.get_page(page_number)
    
    # Stats
    stats = {
        'total_submissions': submissions.count(),
        'pending_submissions': submissions.filter(status='pending').count(),
        'approved_submissions': submissions.filter(status='approved').count(),
        'rejected_submissions': submissions.filter(status='rejected').count(),
    }
    
    return render(request, 'employer_forms.html', {
        'employer': employer,
        'submissions': submissions_page,
        'stats': stats,
        'search_query': search_query,
        'status_filter': status_filter,
    })

@login_required
def broker_dashboard_view(request):
    """Broker dashboard showing all form submissions across employers"""
    if not (request.user.is_superuser or request.user.groups.filter(name='Broker Admin').exists()):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get all form submissions
    submissions = EmployeeFormSubmission.objects.select_related('employer').order_by('-created_at')[:50]
    
    # Stats
    all_submissions = EmployeeFormSubmission.objects.all()
    stats = {
        'total_submissions': all_submissions.count(),
        'pending_submissions': all_submissions.filter(status='pending').count(),
        'approved_submissions': all_submissions.filter(status='approved').count(),
        'total_employers': Employer.objects.count(),
    }
    
    return render(request, 'broker_dashboard.html', {
        'submissions': submissions,
        'stats': stats,
    })

# Employee Portal Views

def employee_portal_login_view(request):
    """Employee portal login and registration page"""
    return render(request, 'employee_portal_login.html')

def employee_portal_dashboard_view(request):
    """Employee portal dashboard - shows status and profile management"""
    return render(request, 'employee_portal_dashboard.html')