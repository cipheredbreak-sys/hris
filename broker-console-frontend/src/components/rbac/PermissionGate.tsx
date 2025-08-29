import React, { ReactNode } from 'react';
import { useRBAC } from '../../contexts/RBACContext';
import { SystemRole, PermissionResource, PermissionAction } from '../../types/rbac';
import { Box, Typography, Alert } from '@mui/material';
import { Lock } from '@mui/icons-material';

interface PermissionGateProps {
  children: ReactNode;
  
  // Permission-based access
  resource?: PermissionResource | string;
  action?: PermissionAction | string;
  
  // Role-based access
  role?: SystemRole | string;
  roles?: (SystemRole | string)[];
  
  // Organization-based access
  organizationId?: string;
  
  // Fallback behavior
  fallback?: ReactNode;
  showAccessDenied?: boolean;
  requireAll?: boolean; // If true, all conditions must be met (AND). If false, any condition (OR)
  
  // Custom permission check function
  customCheck?: () => boolean;
}

/**
 * PermissionGate component controls access to child components based on user permissions
 * 
 * Usage examples:
 * 
 * // Simple permission check
 * <PermissionGate resource="employees" action="create">
 *   <CreateEmployeeButton />
 * </PermissionGate>
 * 
 * // Role-based access
 * <PermissionGate roles={['broker_admin', 'super_admin']}>
 *   <AdminPanel />
 * </PermissionGate>
 * 
 * // Multiple conditions (AND)
 * <PermissionGate 
 *   resource="reports" 
 *   action="view_all" 
 *   role="broker_admin" 
 *   requireAll={true}
 * >
 *   <AdminReports />
 * </PermissionGate>
 * 
 * // With fallback content
 * <PermissionGate 
 *   resource="employees" 
 *   action="create"
 *   fallback={<Typography>You need permission to create employees</Typography>}
 * >
 *   <CreateEmployeeForm />
 * </PermissionGate>
 */
export const PermissionGate: React.FC<PermissionGateProps> = ({
  children,
  resource,
  action,
  role,
  roles,
  organizationId,
  fallback,
  showAccessDenied = false,
  requireAll = false,
  customCheck
}) => {
  const { 
    hasPermission, 
    hasRole, 
    hasAnyRole, 
    canAccessOrganization,
    user,
    userRole 
  } = useRBAC();

  const checkAccess = (): boolean => {
    const conditions: boolean[] = [];

    // Custom check
    if (customCheck) {
      conditions.push(customCheck());
    }

    // Permission check
    if (resource && action) {
      conditions.push(hasPermission(resource, action));
    }

    // Role checks
    if (role) {
      conditions.push(hasRole(role));
    }

    if (roles && roles.length > 0) {
      conditions.push(hasAnyRole(roles));
    }

    // Organization access check
    if (organizationId) {
      conditions.push(canAccessOrganization(organizationId));
    }

    // If no conditions specified, default to authenticated user
    if (conditions.length === 0) {
      return !!user;
    }

    // Apply logic (AND vs OR)
    return requireAll 
      ? conditions.every(condition => condition === true)
      : conditions.some(condition => condition === true);
  };

  const hasAccess = checkAccess();

  if (!hasAccess) {
    if (fallback) {
      return <>{fallback}</>;
    }

    if (showAccessDenied) {
      return (
        <AccessDeniedMessage 
          resource={resource}
          action={action}
          role={role}
          roles={roles}
          userRole={userRole}
        />
      );
    }

    return null;
  }

  return <>{children}</>;
};

interface AccessDeniedMessageProps {
  resource?: string;
  action?: string;
  role?: string;
  roles?: (SystemRole | string)[];
  userRole?: SystemRole | string | null;
}

const AccessDeniedMessage: React.FC<AccessDeniedMessageProps> = ({
  resource,
  action,
  role,
  roles,
  userRole
}) => {
  const getMessage = () => {
    if (resource && action) {
      return `You need permission to ${action} ${resource}.`;
    }
    
    if (role) {
      return `This feature requires ${role} role. Your current role: ${userRole || 'unknown'}`;
    }
    
    if (roles && roles.length > 0) {
      return `This feature requires one of these roles: ${roles.join(', ')}. Your current role: ${userRole || 'unknown'}`;
    }
    
    return 'You do not have permission to access this feature.';
  };

  return (
    <Box sx={{ p: 2, textAlign: 'center' }}>
      <Alert 
        severity="warning" 
        icon={<Lock />}
        sx={{ maxWidth: 400, mx: 'auto' }}
      >
        <Typography variant="body2">
          {getMessage()}
        </Typography>
      </Alert>
    </Box>
  );
};

// Convenience components for common use cases
export const SuperAdminOnly: React.FC<{ children: ReactNode; fallback?: ReactNode }> = ({ 
  children, 
  fallback 
}) => (
  <PermissionGate role={SystemRole.SUPER_ADMIN} fallback={fallback}>
    {children}
  </PermissionGate>
);

export const BrokerOnly: React.FC<{ children: ReactNode; fallback?: ReactNode }> = ({ 
  children, 
  fallback 
}) => (
  <PermissionGate roles={[SystemRole.BROKER_ADMIN, SystemRole.BROKER_USER]} fallback={fallback}>
    {children}
  </PermissionGate>
);

export const EmployerOnly: React.FC<{ children: ReactNode; fallback?: ReactNode }> = ({ 
  children, 
  fallback 
}) => (
  <PermissionGate roles={[SystemRole.EMPLOYER_ADMIN, SystemRole.EMPLOYER_HR]} fallback={fallback}>
    {children}
  </PermissionGate>
);

export const AdminOnly: React.FC<{ children: ReactNode; fallback?: ReactNode }> = ({ 
  children, 
  fallback 
}) => (
  <PermissionGate 
    roles={[SystemRole.SUPER_ADMIN, SystemRole.BROKER_ADMIN, SystemRole.EMPLOYER_ADMIN]} 
    fallback={fallback}
  >
    {children}
  </PermissionGate>
);

export default PermissionGate;