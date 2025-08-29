"""
RBAC Middleware for Django REST Framework
Provides request-level permission checking and role-based filtering
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
from rest_framework.response import Response
import json
import logging
from .rbac_service import rbac_service

logger = logging.getLogger(__name__)

class RBACMiddleware(MiddlewareMixin):
    """
    Middleware to add RBAC context to requests and responses
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request):
        """Add RBAC context to request"""
        if request.user and not request.user.is_anonymous:
            # Add user permissions to request context
            request.rbac_permissions = rbac_service.get_user_permissions(request.user)
            request.rbac_accessible_orgs = rbac_service.get_accessible_organizations(request.user)
            
            # Add permission checking functions to request
            request.has_permission = lambda resource, action, org_id=None: rbac_service.has_permission(
                request.user, resource, action, org_id
            )
            request.has_role = lambda role: rbac_service.has_role(request.user, role)
            request.has_any_role = lambda roles: rbac_service.has_any_role(request.user, roles)
        else:
            # Anonymous user
            request.rbac_permissions = {}
            request.rbac_accessible_orgs = []
            request.has_permission = lambda *args, **kwargs: False
            request.has_role = lambda *args: False
            request.has_any_role = lambda *args: False

    def process_response(self, request, response):
        """Add RBAC headers to response"""
        if hasattr(request, 'user') and request.user and not request.user.is_anonymous:
            profile = getattr(request.user, 'profile', None)
            if profile:
                # Add user role information to response headers
                response['X-User-Role'] = profile.role
                response['X-User-Organization'] = str(profile.organization_id) if profile.organization else ''
                
                # Add permission summary for frontend
                if hasattr(request, 'rbac_permissions'):
                    response['X-User-Permissions'] = json.dumps(list(request.rbac_permissions.keys()))

        return response

class RBACPermissionMiddleware:
    """
    DRF Middleware for automatic permission checking based on view metadata
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # This middleware is primarily for DRF views
        # Most logic is in the decorators and mixins
        return self.get_response(request)

class RBACExceptionMiddleware(MiddlewareMixin):
    """
    Middleware to handle RBAC exceptions and provide consistent error responses
    """
    
    def process_exception(self, request, exception):
        """Handle RBAC-related exceptions"""
        if isinstance(exception, RBACException):
            return JsonResponse(
                {
                    'error': 'Access Denied',
                    'message': str(exception),
                    'code': exception.error_code,
                    'user_role': getattr(request.user.profile, 'role', 'unknown') if hasattr(request, 'user') and request.user and hasattr(request.user, 'profile') else 'anonymous'
                },
                status=403
            )
        return None

class RBACException(Exception):
    """Custom exception for RBAC-related errors"""
    
    def __init__(self, message, error_code='RBAC_ACCESS_DENIED', user_role=None):
        super().__init__(message)
        self.error_code = error_code
        self.user_role = user_role

class RBACAPIMiddleware:
    """
    Middleware specifically for API endpoints that adds RBAC context
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # API endpoints that require special RBAC handling
        self.rbac_endpoints = {
            '/api/broker/': {
                'required_roles': ['broker_admin', 'broker_user', 'super_admin'],
                'resource': 'employers'
            },
            '/api/employees/': {
                'required_roles': ['broker_admin', 'broker_user', 'employer_admin', 'employer_hr', 'employee'],
                'resource': 'employees'
            },
            '/api/plans/': {
                'required_roles': ['broker_admin', 'broker_user', 'employer_admin', 'employee'],
                'resource': 'plans'
            },
            '/api/admin/': {
                'required_roles': ['super_admin'],
                'resource': 'admin'
            }
        }

    def __call__(self, request):
        # Check if this is an API request
        if request.path.startswith('/api/'):
            self._check_api_access(request)
        
        response = self.get_response(request)
        return response

    def _check_api_access(self, request):
        """Check access to API endpoints based on configuration"""
        if not request.user or request.user.is_anonymous:
            return  # Will be handled by authentication middleware
            
        # Find matching endpoint configuration
        endpoint_config = None
        for endpoint_path, config in self.rbac_endpoints.items():
            if request.path.startswith(endpoint_path):
                endpoint_config = config
                break
        
        if endpoint_config:
            required_roles = endpoint_config.get('required_roles', [])
            if required_roles and not rbac_service.has_any_role(request.user, required_roles):
                profile = getattr(request.user, 'profile', None)
                user_role = profile.role if profile else 'unknown'
                
                raise RBACException(
                    f'Access denied. Required roles: {", ".join(required_roles)}. Your role: {user_role}',
                    'RBAC_INSUFFICIENT_ROLE',
                    user_role
                )

def rbac_context_processor(request):
    """
    Context processor to add RBAC information to template context
    For use in Django templates (if needed)
    """
    if not hasattr(request, 'user') or request.user.is_anonymous:
        return {
            'user_role': None,
            'user_permissions': {},
            'user_accessible_orgs': [],
            'rbac_context': {}
        }
    
    profile = getattr(request.user, 'profile', None)
    if not profile:
        return {
            'user_role': None,
            'user_permissions': {},
            'user_accessible_orgs': [],
            'rbac_context': {}
        }
    
    return {
        'user_role': profile.role,
        'user_permissions': rbac_service.get_user_permissions(request.user),
        'user_accessible_orgs': rbac_service.get_accessible_organizations(request.user),
        'rbac_context': {
            'is_super_admin': profile.role == 'super_admin',
            'is_broker_user': profile.role.startswith('broker_') if profile.role else False,
            'is_employer_user': profile.role.startswith('employer_') if profile.role else False,
            'is_employee': profile.role == 'employee',
            'organization_name': profile.organization.name if profile.organization else None,
            'organization_type': profile.organization.type if profile.organization else None
        }
    }

class RBACLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging RBAC-related actions and access attempts
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Paths to log for RBAC auditing
        self.audit_paths = [
            '/api/admin/',
            '/api/users/',
            '/api/roles/',
            '/api/organizations/'
        ]

    def process_request(self, request):
        """Log important RBAC requests"""
        if any(request.path.startswith(path) for path in self.audit_paths):
            if request.user and not request.user.is_anonymous:
                profile = getattr(request.user, 'profile', None)
                user_role = profile.role if profile else 'unknown'
                
                logger.info(
                    f'RBAC Access: {request.method} {request.path} - '
                    f'User: {request.user.username} ({user_role}) - '
                    f'IP: {request.META.get("REMOTE_ADDR", "unknown")}'
                )

    def process_response(self, request, response):
        """Log RBAC responses for auditing"""
        if any(request.path.startswith(path) for path in self.audit_paths):
            if response.status_code == 403:
                logger.warning(
                    f'RBAC Access Denied: {request.method} {request.path} - '
                    f'User: {getattr(request.user, "username", "anonymous")} - '
                    f'Status: {response.status_code}'
                )
        
        return response