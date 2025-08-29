// Django Authentication Types for HRIS Broker Console

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  date_joined: string;
  last_login?: string;
  profile?: UserProfile;
  groups: Group[];
  user_permissions: Permission[];
}

export interface UserProfile {
  id: number;
  user: number;
  phone?: string;
  organization?: Organization;
  role: string;
  title?: string;
  avatar?: string;
  timezone: string;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: number;
  name: string;
  type: 'broker' | 'employer' | 'carrier';
  parent_organization?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Group {
  id: number;
  name: string;
  permissions: Permission[];
}

export interface Permission {
  id: number;
  name: string;
  content_type: number;
  codename: string;
}

// Role-based permission system
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

export enum PermissionAction {
  CREATE = 'add',
  READ = 'view',
  UPDATE = 'change', 
  DELETE = 'delete',
  APPROVE = 'approve',
  EXPORT = 'export',
  IMPORT = 'import'
}

export enum PermissionResource {
  EMPLOYEES = 'employee',
  EMPLOYERS = 'employer',
  PLANS = 'plan',
  ENROLLMENTS = 'enrollment',
  CLAIMS = 'claim',
  REPORTS = 'report',
  USERS = 'user',
  ORGANIZATIONS = 'organization'
}

// API Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface TokenRefreshRequest {
  refresh: string;
}

export interface TokenRefreshResponse {
  access: string;
}

export interface SocialAuthRequest {
  provider: 'google' | 'microsoft';
  access_token: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirmRequest {
  new_password1: string;
  new_password2: string;
  uid: string;
  token: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password1: string;
  new_password2: string;
}

// Context Types
export interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  socialLogin: (provider: 'google' | 'microsoft', accessToken: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  hasPermission: (resource: string, action: string) => boolean;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
  isStaff: () => boolean;
  isSuperUser: () => boolean;
  canAccessResource: (resource: string) => boolean;
}

// Permission checking utilities
export interface PermissionCheck {
  resource: PermissionResource | string;
  action: PermissionAction | string;
  organizationId?: number;
}

// User management types
export interface CreateUserRequest {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  groups?: number[];
  profile?: {
    organization?: number;
    role: string;
    title?: string;
    phone?: string;
  };
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  is_active?: boolean;
  groups?: number[];
  profile?: {
    organization?: number;
    role?: string;
    title?: string;
    phone?: string;
    timezone?: string;
    language?: string;
  };
}

export interface UserListResponse {
  count: number;
  next?: string;
  previous?: string;
  results: User[];
}

// Predefined role permissions mapping
export const ROLE_PERMISSIONS: Record<SystemRole, PermissionCheck[]> = {
  [SystemRole.SUPER_ADMIN]: [
    { resource: '*', action: '*' } // All permissions
  ],
  [SystemRole.BROKER_ADMIN]: [
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.CREATE },
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.READ },
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.UPDATE },
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.DELETE },
    { resource: PermissionResource.EMPLOYERS, action: PermissionAction.CREATE },
    { resource: PermissionResource.EMPLOYERS, action: PermissionAction.READ },
    { resource: PermissionResource.EMPLOYERS, action: PermissionAction.UPDATE },
    { resource: PermissionResource.PLANS, action: PermissionAction.CREATE },
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.PLANS, action: PermissionAction.UPDATE },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.CREATE },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.UPDATE },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.APPROVE },
    { resource: PermissionResource.REPORTS, action: PermissionAction.READ },
    { resource: PermissionResource.REPORTS, action: PermissionAction.EXPORT },
    { resource: PermissionResource.USERS, action: PermissionAction.CREATE },
    { resource: PermissionResource.USERS, action: PermissionAction.READ },
    { resource: PermissionResource.USERS, action: PermissionAction.UPDATE }
  ],
  [SystemRole.BROKER_USER]: [
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.READ },
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.UPDATE },
    { resource: PermissionResource.EMPLOYERS, action: PermissionAction.READ },
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.UPDATE },
    { resource: PermissionResource.REPORTS, action: PermissionAction.READ }
  ],
  [SystemRole.EMPLOYER_ADMIN]: [
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.CREATE },
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.READ },
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.UPDATE },
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.REPORTS, action: PermissionAction.READ }
  ],
  [SystemRole.EMPLOYER_HR]: [
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.READ },
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.UPDATE },
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.REPORTS, action: PermissionAction.READ }
  ],
  [SystemRole.EMPLOYEE]: [
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.UPDATE }
  ],
  [SystemRole.CARRIER_ADMIN]: [
    { resource: PermissionResource.PLANS, action: PermissionAction.CREATE },
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.PLANS, action: PermissionAction.UPDATE },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.CLAIMS, action: PermissionAction.READ },
    { resource: PermissionResource.REPORTS, action: PermissionAction.READ }
  ],
  [SystemRole.CARRIER_USER]: [
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.CLAIMS, action: PermissionAction.READ }
  ],
  [SystemRole.READONLY_USER]: [
    { resource: PermissionResource.EMPLOYEES, action: PermissionAction.READ },
    { resource: PermissionResource.EMPLOYERS, action: PermissionAction.READ },
    { resource: PermissionResource.PLANS, action: PermissionAction.READ },
    { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ },
    { resource: PermissionResource.REPORTS, action: PermissionAction.READ }
  ]
};