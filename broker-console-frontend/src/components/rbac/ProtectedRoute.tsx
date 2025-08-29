import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useRBAC } from '../../contexts/RBACContext';
import { SystemRole, PermissionResource, PermissionAction } from '../../types/rbac';
import { Box, CircularProgress, Alert, AlertTitle } from '@mui/material';
import { Lock, Warning } from '@mui/icons-material';

interface ProtectedRouteProps {
  children: ReactNode;
  
  // Authentication requirements
  requireAuth?: boolean;
  
  // Permission requirements
  resource?: PermissionResource | string;
  action?: PermissionAction | string;
  
  // Role requirements
  role?: SystemRole | string;
  roles?: (SystemRole | string)[];
  
  // Organization access requirements
  organizationId?: string;
  
  // Redirect paths
  loginPath?: string;
  unauthorizedPath?: string;
  fallbackPath?: string;
  
  // Custom validation
  customCheck?: () => boolean;
  
  // Loading and error states
  showLoading?: boolean;
  showUnauthorized?: boolean;
}

/**
 * ProtectedRoute component that guards routes based on authentication and authorization
 * 
 * Usage examples:
 * 
 * // Require authentication only
 * <ProtectedRoute requireAuth>
 *   <Dashboard />
 * </ProtectedRoute>
 * 
 * // Require specific permission
 * <ProtectedRoute resource="employees" action="create">
 *   <CreateEmployeePage />
 * </ProtectedRoute>
 * 
 * // Require specific role
 * <ProtectedRoute roles={['broker_admin', 'super_admin']}>
 *   <AdminDashboard />
 * </ProtectedRoute>
 * 
 * // Multiple requirements with custom redirect
 * <ProtectedRoute 
 *   resource="reports" 
 *   action="view_all"
 *   roles={['broker_admin']}
 *   unauthorizedPath="/access-denied"
 * >
 *   <ReportsPage />
 * </ProtectedRoute>
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAuth = true,
  resource,
  action,
  role,
  roles,
  organizationId,
  loginPath = '/login',
  unauthorizedPath,
  fallbackPath = '/dashboard',
  customCheck,
  showLoading = true,
  showUnauthorized = true
}) => {
  const location = useLocation();
  const { 
    user, 
    loading, 
    hasPermission, 
    hasRole, 
    hasAnyRole, 
    canAccessOrganization,
    userRole 
  } = useRBAC();

  // Show loading state while checking authentication
  if (loading && showLoading) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: '60vh' 
        }}
      >
        <CircularProgress size={40} />
      </Box>
    );
  }

  // Check authentication requirement
  if (requireAuth && !user) {
    return <Navigate to={loginPath} state={{ from: location }} replace />;
  }

  // If no specific authorization requirements, allow access
  if (!resource && !role && !roles && !organizationId && !customCheck) {
    return <>{children}</>;
  }

  const checkAuthorization = (): boolean => {
    // Custom check
    if (customCheck && !customCheck()) {
      return false;
    }

    // Permission check
    if (resource && action && !hasPermission(resource, action)) {
      return false;
    }

    // Role checks
    if (role && !hasRole(role)) {
      return false;
    }

    if (roles && roles.length > 0 && !hasAnyRole(roles)) {
      return false;
    }

    // Organization access check
    if (organizationId && !canAccessOrganization(organizationId)) {
      return false;
    }

    return true;
  };

  const isAuthorized = checkAuthorization();

  if (!isAuthorized) {
    if (unauthorizedPath) {
      return <Navigate to={unauthorizedPath} replace />;
    }

    if (showUnauthorized) {
      return (
        <UnauthorizedAccessMessage 
          resource={resource}
          action={action}
          role={role}
          roles={roles}
          userRole={userRole}
          fallbackPath={fallbackPath}
        />
      );
    }

    return <Navigate to={fallbackPath} replace />;
  }

  return <>{children}</>;
};

interface UnauthorizedAccessMessageProps {
  resource?: string;
  action?: string;
  role?: string;
  roles?: (SystemRole | string)[];
  userRole?: SystemRole | string | null;
  fallbackPath?: string;
}

const UnauthorizedAccessMessage: React.FC<UnauthorizedAccessMessageProps> = ({
  resource,
  action,
  role,
  roles,
  userRole,
  fallbackPath = '/dashboard'
}) => {
  const getMessage = () => {
    if (resource && action) {
      return {
        title: 'Permission Required',
        message: `You need permission to ${action} ${resource} to access this page.`,
        suggestion: 'Please contact your administrator to request the necessary permissions.'
      };
    }
    
    if (role) {
      return {
        title: 'Role Required',
        message: `This page requires ${role} role access.`,
        suggestion: `Your current role is ${userRole || 'unknown'}. Please contact your administrator for role changes.`
      };
    }
    
    if (roles && roles.length > 0) {
      return {
        title: 'Authorized Roles Required',
        message: `This page requires one of these roles: ${roles.join(', ')}.`,
        suggestion: `Your current role is ${userRole || 'unknown'}. Please contact your administrator for role changes.`
      };
    }
    
    return {
      title: 'Access Denied',
      message: 'You do not have permission to access this page.',
      suggestion: 'Please contact your administrator if you believe you should have access.'
    };
  };

  const { title, message, suggestion } = getMessage();

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '60vh',
        p: 3
      }}
    >
      <Alert 
        severity="warning" 
        icon={<Lock />}
        sx={{ maxWidth: 600 }}
        action={
          <Box sx={{ mt: 2 }}>
            <button 
              onClick={() => window.history.back()}
              style={{
                marginRight: 8,
                padding: '6px 16px',
                backgroundColor: 'transparent',
                border: '1px solid #ed6c02',
                color: '#ed6c02',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Go Back
            </button>
            <button 
              onClick={() => window.location.href = fallbackPath}
              style={{
                padding: '6px 16px',
                backgroundColor: '#ed6c02',
                border: 'none',
                color: 'white',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Go to Dashboard
            </button>
          </Box>
        }
      >
        <AlertTitle>{title}</AlertTitle>
        <Box sx={{ mb: 1 }}>
          {message}
        </Box>
        <Box sx={{ fontSize: '0.875rem', opacity: 0.8 }}>
          {suggestion}
        </Box>
      </Alert>
    </Box>
  );
};

// Convenience components for common route protection patterns
export const AdminRoute: React.FC<{ children: ReactNode }> = ({ children }) => (
  <ProtectedRoute 
    roles={[SystemRole.SUPER_ADMIN, SystemRole.BROKER_ADMIN, SystemRole.EMPLOYER_ADMIN]}
  >
    {children}
  </ProtectedRoute>
);

export const SuperAdminRoute: React.FC<{ children: ReactNode }> = ({ children }) => (
  <ProtectedRoute role={SystemRole.SUPER_ADMIN}>
    {children}
  </ProtectedRoute>
);

export const BrokerRoute: React.FC<{ children: ReactNode }> = ({ children }) => (
  <ProtectedRoute 
    roles={[SystemRole.BROKER_ADMIN, SystemRole.BROKER_USER]}
  >
    {children}
  </ProtectedRoute>
);

export const EmployerRoute: React.FC<{ children: ReactNode }> = ({ children }) => (
  <ProtectedRoute 
    roles={[SystemRole.EMPLOYER_ADMIN, SystemRole.EMPLOYER_HR]}
  >
    {children}
  </ProtectedRoute>
);

export const EmployeeRoute: React.FC<{ children: ReactNode }> = ({ children }) => (
  <ProtectedRoute role={SystemRole.EMPLOYEE}>
    {children}
  </ProtectedRoute>
);

// Higher-order component for route protection
export function withRoleProtection<P extends object>(
  Component: React.ComponentType<P>,
  protectionProps: Omit<ProtectedRouteProps, 'children'>
) {
  return function ProtectedComponent(props: P) {
    return (
      <ProtectedRoute {...protectionProps}>
        <Component {...props} />
      </ProtectedRoute>
    );
  };
}

export default ProtectedRoute;