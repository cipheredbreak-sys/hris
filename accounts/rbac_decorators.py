"""
RBAC Decorators and Middleware for Django Views
Provides permission checking decorators for API endpoints
"""
from functools import wraps
from typing import List, Optional, Callable, Any
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser
from rest_framework import status
from rest_framework.response import Response
from .rbac_service import rbac_service
import logging

logger = logging.getLogger(__name__)

def require_permission(resource: str, action: str, organization_param: Optional[str] = None):
    """
    Decorator to require specific permission for view access
    
    Args:
        resource: Resource name (e.g., 'employees', 'plans')
        action: Action name (e.g., 'read', 'create', 'update')
        organization_param: Parameter name containing organization ID
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Check authentication
            if not request.user or isinstance(request.user, AnonymousUser):
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get organization ID from parameters if specified
            organization_id = None
            if organization_param:
                organization_id = kwargs.get(organization_param) or request.data.get(organization_param)
            
            # Check permission
            if not rbac_service.has_permission(request.user, resource, action, organization_id):
                logger.warning(
                    f"Permission denied for user {request.user.id} "
                    f"({request.user.username}) attempting {action} on {resource}"
                )
                return Response(
                    {
                        'error': 'Insufficient permissions',
                        'required_permission': f'{resource}:{action}',
                        'user_role': getattr(request.user.profile, 'role', 'unknown')
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator

def require_role(roles: List[str]):
    """
    Decorator to require specific role(s) for view access
    
    Args:
        roles: List of acceptable role names
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Check authentication
            if not request.user or isinstance(request.user, AnonymousUser):
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check role
            if not rbac_service.has_any_role(request.user, roles):
                user_role = getattr(request.user.profile, 'role', 'unknown') if hasattr(request.user, 'profile') else 'unknown'
                logger.warning(
                    f"Role check failed for user {request.user.id} "
                    f"({request.user.username}) with role {user_role}. Required: {roles}"
                )
                return Response(
                    {
                        'error': 'Insufficient role privileges',
                        'required_roles': roles,
                        'user_role': user_role
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator

def require_self_or_permission(resource: str, action: str, user_id_param: str = 'user_id'):
    """
    Decorator that allows access if user is accessing their own data OR has permission
    
    Args:
        resource: Resource name for permission check
        action: Action name for permission check  
        user_id_param: Parameter name containing target user ID
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Check authentication
            if not request.user or isinstance(request.user, AnonymousUser):
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get target user ID
            target_user_id = kwargs.get(user_id_param) or request.data.get(user_id_param)
            
            # Allow if accessing own data
            if target_user_id and str(request.user.id) == str(target_user_id):
                return view_func(self, request, *args, **kwargs)
            
            # Otherwise check permission
            if not rbac_service.has_permission(request.user, resource, action):
                return Response(
                    {
                        'error': 'Insufficient permissions',
                        'message': 'You can only access your own data or need appropriate permissions'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator

def organization_scoped(organization_param: str = 'organization_id'):
    """
    Decorator to ensure user can only access data from accessible organizations
    
    Args:
        organization_param: Parameter name containing organization ID
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Check authentication
            if not request.user or isinstance(request.user, AnonymousUser):
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Get organization ID
            organization_id = kwargs.get(organization_param) or request.data.get(organization_param)
            
            if organization_id:
                # Check if user can access this organization
                accessible_orgs = rbac_service.get_accessible_organizations(request.user)
                
                if str(organization_id) not in accessible_orgs:
                    return Response(
                        {
                            'error': 'Access denied to organization',
                            'organization_id': organization_id
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator

class RBACViewMixin:
    """Mixin to add RBAC functionality to Django REST Framework ViewSets"""
    
    def check_object_permissions(self, request, obj):
        """Override to add custom object-level permission checks"""
        super().check_object_permissions(request, obj)
        
        # Add custom logic based on object type
        if hasattr(obj, 'organization') or hasattr(obj, 'employer'):
            org_id = getattr(obj, 'organization_id', None) or getattr(obj, 'employer_id', None)
            if org_id:
                accessible_orgs = rbac_service.get_accessible_organizations(request.user)
                if str(org_id) not in accessible_orgs:
                    self.permission_denied(
                        request, 
                        message="You don't have access to this organization's data"
                    )
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Determine resource type from model name
        model_name = queryset.model._meta.model_name
        resource_mapping = {
            'employee': 'employees',
            'employer': 'employers', 
            'plan': 'plans',
            'enrollment': 'enrollments',
            'user': 'users'
        }
        
        resource = resource_mapping.get(model_name, model_name)
        return rbac_service.filter_queryset_by_permissions(
            self.request.user, 
            queryset, 
            resource
        )

def rbac_required(resource: str, action: str):
    """
    Class decorator for ViewSets to add RBAC permission checking
    
    Args:
        resource: Resource name
        action: Action name
    """
    def decorator(cls):
        # Store original methods
        original_dispatch = getattr(cls, 'dispatch', None)
        
        def dispatch(self, request, *args, **kwargs):
            # Check permission before dispatching
            if not rbac_service.has_permission(request.user, resource, action):
                return Response(
                    {'error': 'Insufficient permissions'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Call original dispatch if it exists, otherwise call parent
            if original_dispatch:
                return original_dispatch(self, request, *args, **kwargs)
            else:
                return super(cls, self).dispatch(request, *args, **kwargs)
        
        # Replace dispatch method
        cls.dispatch = dispatch
        return cls
    
    return decorator

# Convenience function for permission checking in templates/frontend
def user_permissions_context(user) -> dict:
    """Get user permissions for template/frontend context"""
    if not user or isinstance(user, AnonymousUser):
        return {}
    
    try:
        profile = getattr(user, 'profile', None)
        if not profile:
            return {}
        
        permissions = rbac_service.get_user_permissions(user)
        accessible_orgs = rbac_service.get_accessible_organizations(user)
        
        return {
            'user_role': profile.role,
            'user_organization': str(profile.organization_id) if profile.organization else None,
            'permissions': permissions,
            'accessible_organizations': accessible_orgs,
            'is_super_admin': profile.role == 'super_admin',
            'is_broker_user': profile.role.startswith('broker_') if profile.role else False,
            'is_employer_user': profile.role.startswith('employer_') if profile.role else False,
            'is_employee': profile.role == 'employee'
        }
    except Exception as e:
        logger.error(f"Error getting user permissions context: {e}")
        return {}