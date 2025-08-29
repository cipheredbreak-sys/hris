from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from .models import Membership, Organization, Role, AuditEvent


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Extract user agent from request."""
    return request.META.get('HTTP_USER_AGENT', '')


def org_scoped(view_func):
    """
    Decorator that ensures the user has access to the requested organization.
    Expects organization_id or org_slug in the URL parameters or request data.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Extract organization identifier from URL kwargs or request data
        org_id = kwargs.get('organization_id') or kwargs.get('org_id')
        org_slug = kwargs.get('organization_slug') or kwargs.get('org_slug')
        
        # If no org identifier in URL, try to get from request data
        if not org_id and not org_slug:
            if request.method == 'GET':
                org_id = request.GET.get('organization_id')
                org_slug = request.GET.get('org_slug')
            else:
                org_id = getattr(request, request.method, {}).get('organization_id')
                org_slug = getattr(request, request.method, {}).get('org_slug')
        
        # Get organization
        organization = None
        if org_id:
            try:
                organization = Organization.objects.get(id=org_id)
            except Organization.DoesNotExist:
                raise Http404("Organization not found")
        elif org_slug:
            try:
                organization = Organization.objects.get(slug=org_slug)
            except Organization.DoesNotExist:
                raise Http404("Organization not found")
        
        if not organization:
            raise PermissionDenied("Organization not specified")
        
        # Check if user has membership in this organization
        try:
            membership = Membership.objects.get(
                user=request.user,
                organization=organization
            )
        except Membership.DoesNotExist:
            # Log permission denied event
            AuditEvent.objects.create(
                user=request.user,
                event='permission_denied',
                organization=organization,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                metadata={
                    'view': view_func.__name__,
                    'reason': 'no_membership'
                }
            )
            raise PermissionDenied("You do not have access to this organization")
        
        # Add membership and organization to request for use in view
        request.current_membership = membership
        request.current_organization = organization
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def requires_role(*required_roles):
    """
    Decorator that requires the user to have one of the specified roles
    in the current organization context.
    """
    def decorator(view_func):
        @wraps(view_func)
        @org_scoped
        def wrapper(request, *args, **kwargs):
            user_role = request.current_membership.role
            
            if user_role not in required_roles:
                # Log permission denied event
                AuditEvent.objects.create(
                    user=request.user,
                    event='permission_denied',
                    organization=request.current_organization,
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    metadata={
                        'view': view_func.__name__,
                        'required_roles': list(required_roles),
                        'user_role': user_role,
                        'reason': 'insufficient_role'
                    }
                )
                raise PermissionDenied(f"This action requires one of: {', '.join(required_roles)}")
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def superuser_required(view_func):
    """
    Decorator that requires the user to be a superuser.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            # Log permission denied event
            AuditEvent.objects.create(
                user=request.user,
                event='permission_denied',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                metadata={
                    'view': view_func.__name__,
                    'reason': 'not_superuser'
                }
            )
            raise PermissionDenied("Superuser access required")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def broker_admin_required(view_func):
    """
    Decorator that requires the user to be a broker admin.
    """
    return requires_role(Role.SUPERUSER, Role.BROKER_ADMIN)(view_func)


def employer_admin_required(view_func):
    """
    Decorator that requires the user to be an employer admin or higher.
    """
    return requires_role(Role.SUPERUSER, Role.BROKER_ADMIN, Role.EMPLOYER_ADMIN)(view_func)


# DRF Permission Classes

class IsInOrganization(permissions.BasePermission):
    """
    Permission class that checks if the user is a member of the organization.
    Expects 'organization_id' or 'org_slug' in the view kwargs.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Extract organization identifier
        org_id = view.kwargs.get('organization_id') or view.kwargs.get('org_id')
        org_slug = view.kwargs.get('organization_slug') or view.kwargs.get('org_slug')
        
        # Get organization
        organization = None
        if org_id:
            try:
                organization = Organization.objects.get(id=org_id)
            except Organization.DoesNotExist:
                return False
        elif org_slug:
            try:
                organization = Organization.objects.get(slug=org_slug)
            except Organization.DoesNotExist:
                return False
        
        if not organization:
            return False
        
        # Check membership
        try:
            membership = Membership.objects.get(
                user=request.user,
                organization=organization
            )
            # Store for use in view
            request.current_membership = membership
            request.current_organization = organization
            return True
        except Membership.DoesNotExist:
            # Log permission denied
            AuditEvent.objects.create(
                user=request.user,
                event='permission_denied',
                organization=organization,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                metadata={
                    'view': view.__class__.__name__,
                    'reason': 'no_membership'
                }
            )
            return False


class HasRole(permissions.BasePermission):
    """
    Permission class that checks if the user has the required role.
    Must be used with IsInOrganization.
    """
    
    required_roles = []  # Override in subclasses
    
    def has_permission(self, request, view):
        if not hasattr(request, 'current_membership'):
            return False
        
        user_role = request.current_membership.role
        
        if user_role not in self.required_roles:
            # Log permission denied
            AuditEvent.objects.create(
                user=request.user,
                event='permission_denied',
                organization=request.current_organization,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                metadata={
                    'view': view.__class__.__name__,
                    'required_roles': list(self.required_roles),
                    'user_role': user_role,
                    'reason': 'insufficient_role'
                }
            )
            return False
        
        return True


class IsSuperuser(permissions.BasePermission):
    """
    Permission class that checks if the user is a superuser.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if not request.user.is_superuser:
            # Log permission denied
            AuditEvent.objects.create(
                user=request.user,
                event='permission_denied',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                metadata={
                    'view': view.__class__.__name__,
                    'reason': 'not_superuser'
                }
            )
            return False
        
        return True


class IsBrokerAdmin(HasRole):
    """Permission class for broker admin access."""
    required_roles = [Role.SUPERUSER, Role.BROKER_ADMIN]


class IsEmployerAdmin(HasRole):
    """Permission class for employer admin access."""
    required_roles = [Role.SUPERUSER, Role.BROKER_ADMIN, Role.EMPLOYER_ADMIN]


class IsEmployee(HasRole):
    """Permission class for employee access."""
    required_roles = [Role.SUPERUSER, Role.BROKER_ADMIN, Role.EMPLOYER_ADMIN, Role.EMPLOYEE]


# Composite permission classes

class OrganizationScopedPermission(permissions.BasePermission):
    """
    Base class for organization-scoped permissions.
    Combines IsInOrganization with role checking.
    """
    
    required_roles = []
    
    def has_permission(self, request, view):
        # First check organization membership
        org_permission = IsInOrganization()
        if not org_permission.has_permission(request, view):
            return False
        
        # Then check role
        if not self.required_roles:
            return True  # Just membership required
        
        user_role = request.current_membership.role
        return user_role in self.required_roles


class BrokerAdminPermission(OrganizationScopedPermission):
    """Combined permission for broker admin access."""
    required_roles = [Role.SUPERUSER, Role.BROKER_ADMIN]


class EmployerAdminPermission(OrganizationScopedPermission):
    """Combined permission for employer admin access."""
    required_roles = [Role.SUPERUSER, Role.BROKER_ADMIN, Role.EMPLOYER_ADMIN]


class EmployeePermission(OrganizationScopedPermission):
    """Combined permission for employee access."""
    required_roles = [Role.SUPERUSER, Role.BROKER_ADMIN, Role.EMPLOYER_ADMIN, Role.EMPLOYEE]


# Utility functions for permission checking

def user_has_role_in_org(user, organization, required_roles):
    """
    Check if user has one of the required roles in the organization.
    """
    try:
        membership = Membership.objects.get(user=user, organization=organization)
        return membership.role in required_roles
    except Membership.DoesNotExist:
        return False


def get_user_organizations(user):
    """
    Get all organizations the user is a member of.
    """
    return Organization.objects.filter(memberships__user=user)


def get_user_role_in_org(user, organization):
    """
    Get user's role in a specific organization.
    """
    try:
        membership = Membership.objects.get(user=user, organization=organization)
        return membership.role
    except Membership.DoesNotExist:
        return None


def filter_queryset_by_organization(queryset, user, organization_field='organization'):
    """
    Filter queryset to only include objects from organizations the user has access to.
    """
    if user.is_superuser:
        return queryset
    
    user_orgs = get_user_organizations(user)
    filter_kwargs = {f'{organization_field}__in': user_orgs}
    return queryset.filter(**filter_kwargs)