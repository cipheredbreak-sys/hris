// RBAC Type Definitions for HRIS Broker Console

export interface User {
  uid: string;
  email: string;
  displayName: string;
  photoURL?: string;
  roles: string[];
  permissions: string[];
  organizationId?: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
  lastLoginAt?: Date;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  organizationId?: string; // null for system-wide roles
  isSystemRole: boolean;
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string; // e.g., 'employees', 'employers', 'plans'
  action: string;   // e.g., 'read', 'write', 'delete', 'approve'
  category: 'system' | 'organization' | 'data';
}

export interface Organization {
  id: string;
  name: string;
  type: 'broker' | 'employer' | 'carrier';
  parentOrganizationId?: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// Predefined System Roles
export enum SystemRole {
  SUPER_ADMIN = 'super_admin',
  BROKER_ADMIN = 'broker_admin',
  BROKER_USER = 'broker_user',
  EMPLOYER_ADMIN = 'employer_admin',
  EMPLOYER_HR = 'employer_hr',
  EMPLOYEE = 'employee',
  CARRIER_ADMIN = 'carrier_admin',
  CARRIER_USER = 'carrier_user',
  READONLY_USER = 'readonly_user'
}

// Permission Categories and Actions
export enum PermissionResource {
  EMPLOYEES = 'employees',
  EMPLOYERS = 'employers',
  PLANS = 'plans',
  ENROLLMENTS = 'enrollments',
  CLAIMS = 'claims',
  REPORTS = 'reports',
  USERS = 'users',
  ROLES = 'roles',
  ORGANIZATIONS = 'organizations',
  SETTINGS = 'settings',
  BILLING = 'billing',
  INTEGRATIONS = 'integrations'
}

export enum PermissionAction {
  CREATE = 'create',
  READ = 'read',
  UPDATE = 'update',
  DELETE = 'delete',
  APPROVE = 'approve',
  REJECT = 'reject',
  EXPORT = 'export',
  IMPORT = 'import',
  MANAGE = 'manage',
  VIEW_ALL = 'view_all',
  VIEW_OWN = 'view_own'
}

// Context and Hook Types
export interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  hasPermission: (resource: string, action: string) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  refreshUser: () => Promise<void>;
}

export interface RBACContextType {
  permissions: Permission[];
  roles: Role[];
  organizations: Organization[];
  loadPermissions: () => Promise<void>;
  loadRoles: () => Promise<void>;
  loadOrganizations: () => Promise<void>;
  createRole: (role: Omit<Role, 'id' | 'createdAt' | 'updatedAt'>) => Promise<Role>;
  updateRole: (id: string, updates: Partial<Role>) => Promise<void>;
  deleteRole: (id: string) => Promise<void>;
  assignRole: (userId: string, roleId: string) => Promise<void>;
  revokeRole: (userId: string, roleId: string) => Promise<void>;
  checkPermission: (userId: string, resource: string, action: string) => Promise<boolean>;
}

// API Response Types
export interface RoleAssignment {
  userId: string;
  roleId: string;
  organizationId?: string;
  assignedBy: string;
  assignedAt: Date;
  expiresAt?: Date;
}

export interface UserRoleInfo {
  user: User;
  roles: Role[];
  effectivePermissions: Permission[];
  organizationRoles: { [orgId: string]: Role[] };
}

// Utility Types
export type PermissionCheck = {
  resource: PermissionResource | string;
  action: PermissionAction | string;
  organizationId?: string;
};

export type RolePermissionMatrix = {
  [roleId: string]: {
    [resource: string]: string[]; // array of actions
  };
};

// Predefined Permission Sets
export const BROKER_ADMIN_PERMISSIONS: PermissionCheck[] = [
  { resource: PermissionResource.EMPLOYEES, action: PermissionAction.MANAGE },
  { resource: PermissionResource.EMPLOYERS, action: PermissionAction.MANAGE },
  { resource: PermissionResource.PLANS, action: PermissionAction.MANAGE },
  { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.MANAGE },
  { resource: PermissionResource.REPORTS, action: PermissionAction.VIEW_ALL },
  { resource: PermissionResource.USERS, action: PermissionAction.MANAGE },
  { resource: PermissionResource.ROLES, action: PermissionAction.MANAGE },
  { resource: PermissionResource.SETTINGS, action: PermissionAction.MANAGE }
];

export const BROKER_USER_PERMISSIONS: PermissionCheck[] = [
  { resource: PermissionResource.EMPLOYEES, action: PermissionAction.READ },
  { resource: PermissionResource.EMPLOYEES, action: PermissionAction.UPDATE },
  { resource: PermissionResource.EMPLOYERS, action: PermissionAction.READ },
  { resource: PermissionResource.EMPLOYERS, action: PermissionAction.UPDATE },
  { resource: PermissionResource.PLANS, action: PermissionAction.READ },
  { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.MANAGE },
  { resource: PermissionResource.REPORTS, action: PermissionAction.READ }
];

export const EMPLOYER_ADMIN_PERMISSIONS: PermissionCheck[] = [
  { resource: PermissionResource.EMPLOYEES, action: PermissionAction.MANAGE },
  { resource: PermissionResource.PLANS, action: PermissionAction.READ },
  { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
  { resource: PermissionResource.REPORTS, action: PermissionAction.VIEW_OWN },
  { resource: PermissionResource.USERS, action: PermissionAction.VIEW_OWN }
];

export const EMPLOYEE_PERMISSIONS: PermissionCheck[] = [
  { resource: PermissionResource.EMPLOYEES, action: PermissionAction.VIEW_OWN },
  { resource: PermissionResource.PLANS, action: PermissionAction.READ },
  { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.VIEW_OWN },
  { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.UPDATE }
];