import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { SystemRole, PermissionResource, PermissionAction, User, Permission } from '../types/rbac';
import { useAuth } from './AuthContext';

interface RBACContextType {
  user: User | null;
  userRole: SystemRole | null;
  permissions: Permission[];
  loading: boolean;
  error: string | null;
  
  // Permission checking methods
  hasPermission: (resource: PermissionResource | string, action: PermissionAction | string) => boolean;
  hasRole: (role: SystemRole | string) => boolean;
  hasAnyRole: (roles: (SystemRole | string)[]) => boolean;
  canAccessResource: (resource: string) => boolean;
  canPerformAction: (resource: string, action: string) => boolean;
  
  // Organization/tenant methods
  canAccessOrganization: (organizationId: string) => boolean;
  getAccessibleOrganizations: () => string[];
  
  // User management methods
  canManageUser: (targetUserId: string) => boolean;
  canAssignRole: (targetRole: SystemRole | string) => boolean;
  
  // UI helper methods
  filterMenuItems: (menuItems: NavigationMenuItem[]) => NavigationMenuItem[];
  getPermissionLevel: () => number;
  
  // Data loading
  refreshPermissions: () => Promise<void>;
}

export interface NavigationMenuItem {
  id: string;
  label: string;
  path: string;
  icon?: string | React.ReactElement;
  requiredPermission?: {
    resource: string;
    action: string;
  };
  requiredRole?: SystemRole | string;
  requiredRoles?: (SystemRole | string)[];
  children?: NavigationMenuItem[];
}

interface RBACProviderProps {
  children: ReactNode;
}

const RBACContext = createContext<RBACContextType | undefined>(undefined);

// Role hierarchy for permission level calculation
const ROLE_HIERARCHY: Record<string, number> = {
  [SystemRole.EMPLOYEE]: 1,
  [SystemRole.EMPLOYER_HR]: 2,
  [SystemRole.EMPLOYER_ADMIN]: 3,
  [SystemRole.BROKER_USER]: 4,
  [SystemRole.BROKER_ADMIN]: 5,
  [SystemRole.CARRIER_USER]: 6,
  [SystemRole.CARRIER_ADMIN]: 7,
  [SystemRole.SUPER_ADMIN]: 10
};

// Default permissions by role
const ROLE_PERMISSIONS: Record<string, { resource: string; action: string }[]> = {
  [SystemRole.SUPER_ADMIN]: [
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.MANAGE },
    { resource: PermissionResource.EMPLOYERS, action: PermissionAction.MANAGE },
    { resource: PermissionResource.PLANS, action: PermissionAction.MANAGE },
    { resource: PermissionResource.USERS, action: PermissionAction.MANAGE },
    { resource: PermissionResource.ROLES, action: PermissionAction.MANAGE },
    { resource: PermissionResource.ORGANIZATIONS, action: PermissionAction.MANAGE },
    { resource: PermissionResource.SETTINGS, action: PermissionAction.MANAGE },
    { resource: PermissionResource.REPORTS, action: PermissionAction.VIEW_ALL }
  ],
  [SystemRole.BROKER_ADMIN]: [
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.MANAGE },
    { resource: PermissionResource.EMPLOYERS, action: PermissionAction.MANAGE },
    { resource: PermissionResource.PLANS, action: PermissionAction.MANAGE },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.USERS, action: PermissionAction.CREATE },
    { resource: PermissionResource.USERS, action: PermissionAction.UPDATE },
    { resource: PermissionResource.REPORTS, action: PermissionAction.EXPORT },
    { resource: PermissionResource.SETTINGS, action: PermissionAction.UPDATE }
  ],
  [SystemRole.BROKER_USER]: [
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.READ },
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.UPDATE },
    { resource: PermissionResource.EMPLOYERS, action: PermissionAction.READ },
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.REPORTS, action: PermissionAction.READ }
  ],
  [SystemRole.EMPLOYER_ADMIN]: [
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.MANAGE },
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.USERS, action: PermissionAction.CREATE },
    { resource: PermissionResource.USERS, action: PermissionAction.UPDATE },
    { resource: PermissionResource.REPORTS, action: PermissionAction.VIEW_OWN },
    { resource: PermissionResource.SETTINGS, action: PermissionAction.UPDATE }
  ],
  [SystemRole.EMPLOYER_HR]: [
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.READ },
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.UPDATE },
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.REPORTS, action: PermissionAction.VIEW_OWN }
  ],
  [SystemRole.EMPLOYEE]: [
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.VIEW_OWN },
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.VIEW_OWN },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.UPDATE }
  ]
};

export const RBACProvider: React.FC<RBACProviderProps> = ({ children }) => {
  const { user: authUser } = useAuth();
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Convert AuthContext user to RBAC User format
  const user: User | null = authUser ? {
    uid: authUser.id,
    email: authUser.email,
    displayName: `${authUser.firstName} ${authUser.lastName}`,
    roles: [authUser.role],
    permissions: [],
    organizationId: 'default-org', // TODO: Add organizationId to AuthContext user
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
  } : null;

  const userRole = user?.roles?.[0] as SystemRole || null;

  // Load permissions when user changes
  useEffect(() => {
    if (user && userRole) {
      loadUserPermissions();
    } else {
      setPermissions([]);
    }
  }, [user, userRole]);

  const loadUserPermissions = async () => {
    if (!user || !userRole) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Get permissions from role defaults (in real app, fetch from API)
      const rolePerms = ROLE_PERMISSIONS[userRole] || [];
      const permissionObjects: Permission[] = rolePerms.map((perm, index) => ({
        id: `${userRole}_${index}`,
        name: `${perm.resource}_${perm.action}`,
        description: `${perm.action} permission for ${perm.resource}`,
        resource: perm.resource,
        action: perm.action,
        category: 'organization' as const
      }));
      
      setPermissions(permissionObjects);
    } catch (err) {
      setError('Failed to load user permissions');
      console.error('Error loading permissions:', err);
    } finally {
      setLoading(false);
    }
  };

  const hasPermission = (resource: PermissionResource | string, action: PermissionAction | string): boolean => {
    if (!user || !userRole) return false;
    
    // Super admin has all permissions
    if (userRole === SystemRole.SUPER_ADMIN) return true;
    
    // Check if user has specific permission
    return permissions.some(perm => 
      perm.resource === resource && 
      (perm.action === action || perm.action === PermissionAction.MANAGE)
    );
  };

  const hasRole = (role: SystemRole | string): boolean => {
    return userRole === role;
  };

  const hasAnyRole = (roles: (SystemRole | string)[]): boolean => {
    return userRole ? roles.includes(userRole) : false;
  };

  const canAccessResource = (resource: string): boolean => {
    return permissions.some(perm => perm.resource === resource);
  };

  const canPerformAction = (resource: string, action: string): boolean => {
    return hasPermission(resource, action);
  };

  const canAccessOrganization = (organizationId: string): boolean => {
    if (!user) return false;
    
    // Super admin can access all organizations
    if (userRole === SystemRole.SUPER_ADMIN) return true;
    
    // Users can access their own organization
    if (user.organizationId === organizationId) return true;
    
    // Broker users can access their employers (would need to check via API)
    if (userRole === SystemRole.BROKER_ADMIN || userRole === SystemRole.BROKER_USER) {
      // In real implementation, check if organizationId is an employer under this broker
      return true; // Placeholder
    }
    
    return false;
  };

  const getAccessibleOrganizations = (): string[] => {
    if (!user) return [];
    
    // Super admin can access all (would fetch from API)
    if (userRole === SystemRole.SUPER_ADMIN) return [];
    
    // Return user's organization and any accessible ones
    const accessible = user.organizationId ? [user.organizationId] : [];
    
    // Broker users would get their employer organizations too
    if (userRole === SystemRole.BROKER_ADMIN || userRole === SystemRole.BROKER_USER) {
      // In real implementation, fetch from API
    }
    
    return accessible;
  };

  const canManageUser = (targetUserId: string): boolean => {
    if (!user) return false;
    
    // Can't manage yourself for role changes
    if (user.uid === targetUserId) return false;
    
    // Check if user has user management permissions
    return hasPermission(PermissionResource.USERS, PermissionAction.MANAGE) ||
           hasPermission(PermissionResource.USERS, PermissionAction.UPDATE);
  };

  const canAssignRole = (targetRole: SystemRole | string): boolean => {
    if (!user || !userRole) return false;
    
    // Super admin can assign any role
    if (userRole === SystemRole.SUPER_ADMIN) return true;
    
    const userLevel = ROLE_HIERARCHY[userRole] || 0;
    const targetLevel = ROLE_HIERARCHY[targetRole] || 0;
    
    // Can only assign roles with lower hierarchy level
    return userLevel > targetLevel && hasPermission(PermissionResource.ROLES, PermissionAction.CREATE);
  };

  const filterMenuItems = (menuItems: NavigationMenuItem[]): NavigationMenuItem[] => {
    if (!user) return [];
    
    return menuItems.filter(item => {
      // Check role requirement
      if (item.requiredRole && !hasRole(item.requiredRole)) {
        return false;
      }
      
      if (item.requiredRoles && !hasAnyRole(item.requiredRoles)) {
        return false;
      }
      
      // Check permission requirement
      if (item.requiredPermission) {
        const { resource, action } = item.requiredPermission;
        if (!hasPermission(resource, action)) {
          return false;
        }
      }
      
      // Recursively filter children
      if (item.children) {
        item.children = filterMenuItems(item.children);
        // Hide parent if no children are accessible
        return item.children.length > 0;
      }
      
      return true;
    });
  };

  const getPermissionLevel = (): number => {
    return userRole ? ROLE_HIERARCHY[userRole] || 0 : 0;
  };

  const refreshPermissions = async (): Promise<void> => {
    await loadUserPermissions();
  };

  const contextValue: RBACContextType = {
    user,
    userRole,
    permissions,
    loading,
    error,
    hasPermission,
    hasRole,
    hasAnyRole,
    canAccessResource,
    canPerformAction,
    canAccessOrganization,
    getAccessibleOrganizations,
    canManageUser,
    canAssignRole,
    filterMenuItems,
    getPermissionLevel,
    refreshPermissions
  };

  return (
    <RBACContext.Provider value={contextValue}>
      {children}
    </RBACContext.Provider>
  );
};

export const useRBAC = (): RBACContextType => {
  const context = useContext(RBACContext);
  if (!context) {
    throw new Error('useRBAC must be used within an RBACProvider');
  }
  return context;
};

// Utility hooks for common permission checks
export const usePermission = (resource: PermissionResource | string, action: PermissionAction | string) => {
  const { hasPermission } = useRBAC();
  return hasPermission(resource, action);
};

export const useRole = (role: SystemRole | string) => {
  const { hasRole } = useRBAC();
  return hasRole(role);
};

export const useAnyRole = (roles: (SystemRole | string)[]) => {
  const { hasAnyRole } = useRBAC();
  return hasAnyRole(roles);
};

export default RBACContext;