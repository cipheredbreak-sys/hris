"""
Role-Based Access Control Service
Handles permission checking, role management, and access control logic
"""
from typing import List, Dict, Optional, Union
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.db import transaction
from .models import UserProfile, Organization, RolePermissionMatrix, AuditLog
import logging

logger = logging.getLogger(__name__)

class RBACService:
    """Service for managing role-based access control"""
    
    # Role hierarchy (higher values have more permissions)
    ROLE_HIERARCHY = {
        'employee': 1,
        'employer_hr': 2,
        'employer_admin': 3,
        'broker_user': 4,
        'broker_admin': 5,
        'carrier_user': 6,
        'carrier_admin': 7,
        'super_admin': 10
    }
    
    # Role permissions matrix
    ROLE_PERMISSIONS = {
        'super_admin': {
            'employees': ['create', 'read', 'update', 'delete', 'manage'],
            'employers': ['create', 'read', 'update', 'delete', 'manage'],
            'plans': ['create', 'read', 'update', 'delete', 'manage'],
            'enrollments': ['create', 'read', 'update', 'delete', 'manage'],
            'users': ['create', 'read', 'update', 'delete', 'manage'],
            'roles': ['create', 'read', 'update', 'delete', 'manage'],
            'organizations': ['create', 'read', 'update', 'delete', 'manage'],
            'settings': ['create', 'read', 'update', 'delete', 'manage'],
            'reports': ['read', 'export', 'view_all'],
            'billing': ['read', 'update', 'manage']
        },
        'broker_admin': {
            'employees': ['create', 'read', 'update', 'delete'],
            'employers': ['create', 'read', 'update', 'delete'],
            'plans': ['create', 'read', 'update', 'delete'],
            'enrollments': ['read', 'update', 'export'],
            'users': ['create', 'read', 'update'],  # Only for their org
            'reports': ['read', 'export', 'view_org'],
            'settings': ['read', 'update']
        },
        'broker_user': {
            'employees': ['read', 'update'],
            'employers': ['read', 'update'],
            'plans': ['read'],
            'enrollments': ['read', 'update'],
            'reports': ['read', 'view_assigned']
        },
        'employer_admin': {
            'employees': ['create', 'read', 'update'],  # Only own employees
            'plans': ['read'],
            'enrollments': ['read'],
            'users': ['create', 'read', 'update'],  # Only HR users in own org
            'reports': ['read', 'view_own'],
            'settings': ['read', 'update']  # Only own employer settings
        },
        'employer_hr': {
            'employees': ['read', 'update'],  # Only own employees
            'plans': ['read'],
            'enrollments': ['read'],
            'reports': ['read', 'view_own']
        },
        'employee': {
            'employees': ['view_own'],  # Only own profile
            'plans': ['read'],  # Available plans
            'enrollments': ['view_own', 'update_own']  # Own enrollment only
        },
        'carrier_admin': {
            'plans': ['create', 'read', 'update', 'delete'],  # Own carrier plans
            'enrollments': ['read'],  # Enrollments for their plans
            'reports': ['read', 'view_carrier']
        },
        'carrier_user': {
            'plans': ['read'],  # Own carrier plans
            'enrollments': ['read'],  # Limited access
            'reports': ['read']
        },
        'readonly_user': {
            'employees': ['read'],
            'employers': ['read'],
            'plans': ['read'],
            'enrollments': ['read'],
            'reports': ['read']
        }
    }

    def __init__(self):
        self.setup_default_permissions()

    def setup_default_permissions(self):
        """Setup default role permission matrix in database"""
        try:
            for role, resources in self.ROLE_PERMISSIONS.items():
                for resource, actions in resources.items():
                    for action in actions:
                        RolePermissionMatrix.objects.get_or_create(
                            role=role,
                            resource=resource,
                            action=action
                        )
        except Exception as e:
            logger.error(f"Error setting up default permissions: {e}")

    def has_permission(self, user: User, resource: str, action: str, organization_id: Optional[str] = None) -> bool:
        """
        Check if user has permission to perform action on resource
        
        Args:
            user: Django User object
            resource: Resource name (e.g., 'employees', 'plans')
            action: Action name (e.g., 'read', 'create', 'update')
            organization_id: Optional organization context
            
        Returns:
            bool: True if user has permission
        """
        try:
            # Get user profile and role
            profile = getattr(user, 'profile', None)
            if not profile:
                return False
                
            role = profile.role
            user_org_id = str(profile.organization_id) if profile.organization else None
            
            # Super admin has all permissions
            if role == 'super_admin':
                return True
                
            # Check if role has the permission
            role_permissions = self.ROLE_PERMISSIONS.get(role, {})
            resource_permissions = role_permissions.get(resource, [])
            
            if action not in resource_permissions:
                return False
                
            # Check organization context for scoped permissions
            if organization_id and user_org_id:
                # For actions that require organization matching
                org_scoped_actions = ['create', 'update', 'delete', 'manage']
                if action in org_scoped_actions:
                    # Broker users can access their employers
                    if role.startswith('broker_') and self._user_can_access_employer(user, organization_id):
                        return True
                    # Employer users can only access their own org
                    elif role.startswith('employer_') and user_org_id == organization_id:
                        return True
                    # Employees can only access their own data
                    elif role == 'employee' and user_org_id == organization_id:
                        return True
                    else:
                        return False
                        
            return True
            
        except Exception as e:
            logger.error(f"Error checking permission for user {user.id}: {e}")
            return False

    def _user_can_access_employer(self, user: User, employer_id: str) -> bool:
        """Check if broker user can access specific employer"""
        try:
            from broker_console.models import Employer
            profile = user.profile
            if not profile.organization:
                return False
                
            # Check if employer belongs to broker's organization
            return Employer.objects.filter(
                id=employer_id,
                broker=profile.organization
            ).exists()
        except Exception:
            return False

    def has_role(self, user: User, role: str) -> bool:
        """Check if user has specific role"""
        try:
            profile = getattr(user, 'profile', None)
            return profile and profile.role == role
        except Exception:
            return False

    def has_any_role(self, user: User, roles: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        try:
            profile = getattr(user, 'profile', None)
            return profile and profile.role in roles
        except Exception:
            return False

    def get_user_permissions(self, user: User) -> Dict[str, List[str]]:
        """Get all permissions for a user"""
        try:
            profile = getattr(user, 'profile', None)
            if not profile:
                return {}
                
            role = profile.role
            return self.ROLE_PERMISSIONS.get(role, {})
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return {}

    def assign_role(self, user: User, role: str, assigned_by: User, organization: Optional[Organization] = None) -> bool:
        """Assign role to user with audit logging"""
        try:
            with transaction.atomic():
                profile, created = UserProfile.objects.get_or_create(user=user)
                old_role = profile.role
                profile.role = role
                
                if organization:
                    profile.organization = organization
                    
                profile.save()
                
                # Log the role change
                AuditLog.objects.create(
                    user=assigned_by,
                    action='role_change',
                    resource_type='UserProfile',
                    resource_id=str(profile.id),
                    description=f'Changed role from {old_role} to {role} for user {user.username}',
                    additional_data={
                        'old_role': old_role,
                        'new_role': role,
                        'target_user': user.username,
                        'organization_id': str(organization.id) if organization else None
                    }
                )
                
                return True
        except Exception as e:
            logger.error(f"Error assigning role: {e}")
            return False

    def get_role_hierarchy_level(self, role: str) -> int:
        """Get numeric level for role hierarchy"""
        return self.ROLE_HIERARCHY.get(role, 0)

    def can_manage_user(self, manager: User, target_user: User) -> bool:
        """Check if manager can manage target user based on role hierarchy"""
        try:
            manager_profile = getattr(manager, 'profile', None)
            target_profile = getattr(target_user, 'profile', None)
            
            if not manager_profile or not target_profile:
                return False
                
            manager_level = self.get_role_hierarchy_level(manager_profile.role)
            target_level = self.get_role_hierarchy_level(target_profile.role)
            
            # Can only manage users with lower hierarchy level
            if manager_level <= target_level:
                return False
                
            # Organization context check
            manager_org = manager_profile.organization
            target_org = target_profile.organization
            
            # Super admin can manage anyone
            if manager_profile.role == 'super_admin':
                return True
                
            # Same organization check for non-super-admin roles
            return manager_org == target_org
            
        except Exception as e:
            logger.error(f"Error checking user management permission: {e}")
            return False

    def get_accessible_organizations(self, user: User) -> List[str]:
        """Get list of organization IDs user can access"""
        try:
            profile = getattr(user, 'profile', None)
            if not profile:
                return []
                
            role = profile.role
            user_org = profile.organization
            
            # Super admin can access all organizations
            if role == 'super_admin':
                return list(Organization.objects.filter(is_active=True).values_list('id', flat=True))
                
            # Broker users can access their broker org and all associated employers
            elif role.startswith('broker_'):
                if user_org and user_org.type == 'broker':
                    accessible_orgs = [str(user_org.id)]
                    # Add all employers under this broker
                    from broker_console.models import Employer
                    employer_ids = Employer.objects.filter(
                        broker_id=user_org.id
                    ).values_list('id', flat=True)
                    accessible_orgs.extend([str(emp_id) for emp_id in employer_ids])
                    return accessible_orgs
                    
            # Other users can only access their own organization
            elif user_org:
                return [str(user_org.id)]
                
            return []
        except Exception as e:
            logger.error(f"Error getting accessible organizations: {e}")
            return []

    def filter_queryset_by_permissions(self, user: User, queryset, resource: str):
        """Filter queryset based on user permissions and organization access"""
        try:
            profile = getattr(user, 'profile', None)
            if not profile:
                return queryset.none()
                
            role = profile.role
            
            # Super admin sees everything
            if role == 'super_admin':
                return queryset
                
            # Get accessible organizations
            accessible_orgs = self.get_accessible_organizations(user)
            
            # Apply filters based on resource type and role
            if resource == 'employees':
                # Employees can only see themselves
                if role == 'employee':
                    return queryset.filter(user=user)
                # Others see employees in accessible organizations
                else:
                    return queryset.filter(employer_id__in=accessible_orgs)
                    
            elif resource == 'employers':
                if role.startswith('broker_'):
                    # Brokers see their employers
                    return queryset.filter(broker=profile.organization)
                elif role.startswith('employer_'):
                    # Employers see only their own organization
                    return queryset.filter(id=profile.organization_id)
                    
            elif resource == 'enrollments':
                if role == 'employee':
                    # Employees see only their enrollments
                    return queryset.filter(employee__user=user)
                else:
                    # Others see enrollments in accessible organizations
                    return queryset.filter(employee__employer_id__in=accessible_orgs)
                    
            return queryset.filter(organization_id__in=accessible_orgs)
            
        except Exception as e:
            logger.error(f"Error filtering queryset: {e}")
            return queryset.none()

# Global instance
rbac_service = RBACService()