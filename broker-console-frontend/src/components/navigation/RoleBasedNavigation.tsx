import React, { useMemo } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  Chip,
  Badge,
  Collapse,
  IconButton,
  Avatar,
  Menu,
  MenuItem
} from '@mui/material';
import {
  Dashboard,
  People,
  Business,
  Assignment,
  Assessment,
  Settings,
  ExpandLess,
  ExpandMore,
  AccountCircle,
  ExitToApp,
  Security,
  AdminPanelSettings,
  Work,
  Person,
  Group,
  InsertChart,
  Description,
  NotificationsActive
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useRBAC, NavigationMenuItem } from '../../contexts/RBACContext';
import { useAuth } from '../../contexts/AuthContext';
import { SystemRole, PermissionResource, PermissionAction } from '../../types/rbac';
import { PermissionGate } from '../rbac/PermissionGate';

const DRAWER_WIDTH = 280;

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ReactElement;
  path: string;
  badge?: number;
  requiredPermission?: {
    resource: PermissionResource | string;
    action: PermissionAction | string;
  };
  requiredRole?: SystemRole | string;
  requiredRoles?: (SystemRole | string)[];
  children?: NavigationItem[];
  dividerAfter?: boolean;
}

const NAVIGATION_ITEMS: NavigationItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <Dashboard />,
    path: '/dashboard'
  },
  
  // Super Admin Section
  {
    id: 'system-admin',
    label: 'System Administration',
    icon: <AdminPanelSettings />,
    path: '/admin',
    requiredRole: SystemRole.SUPER_ADMIN,
    children: [
      {
        id: 'organizations',
        label: 'Organizations',
        icon: <Business />,
        path: '/admin/organizations',
        requiredPermission: { resource: PermissionResource.ORGANIZATIONS, action: PermissionAction.MANAGE }
      },
      {
        id: 'users',
        label: 'User Management',
        icon: <People />,
        path: '/admin/users',
        requiredPermission: { resource: PermissionResource.USERS, action: PermissionAction.MANAGE }
      },
      {
        id: 'roles',
        label: 'Roles & Permissions',
        icon: <Security />,
        path: '/admin/roles',
        requiredPermission: { resource: PermissionResource.ROLES, action: PermissionAction.MANAGE }
      }
    ],
    dividerAfter: true
  },

  // Broker Section
  {
    id: 'employers',
    label: 'Employers',
    icon: <Business />,
    path: '/employers',
    requiredRoles: [SystemRole.BROKER_ADMIN, SystemRole.BROKER_USER],
    children: [
      {
        id: 'employer-list',
        label: 'All Employers',
        icon: <Business />,
        path: '/employers/list',
        requiredPermission: { resource: PermissionResource.EMPLOYERS, action: PermissionAction.READ }
      },
      {
        id: 'create-employer',
        label: 'Add New Employer',
        icon: <Business />,
        path: '/employers/create',
        requiredPermission: { resource: PermissionResource.EMPLOYERS, action: PermissionAction.CREATE }
      }
    ]
  },

  {
    id: 'employees',
    label: 'Employees',
    icon: <People />,
    path: '/employees',
    children: [
      {
        id: 'employee-list',
        label: 'All Employees',
        icon: <People />,
        path: '/employees/list',
        requiredPermission: { resource: PermissionResource.EMPLOYEES, action: PermissionAction.READ }
      },
      {
        id: 'import-employees',
        label: 'Import Employees',
        icon: <People />,
        path: '/employees/import',
        requiredPermission: { resource: PermissionResource.EMPLOYEES, action: PermissionAction.CREATE }
      }
    ]
  },

  {
    id: 'plans',
    label: 'Benefit Plans',
    icon: <Assignment />,
    path: '/plans',
    children: [
      {
        id: 'plan-catalog',
        label: 'Plan Catalog',
        icon: <Assignment />,
        path: '/plans/catalog',
        requiredPermission: { resource: PermissionResource.PLANS, action: PermissionAction.READ }
      },
      {
        id: 'create-plan',
        label: 'Create Plan',
        icon: <Assignment />,
        path: '/plans/create',
        requiredPermission: { resource: PermissionResource.PLANS, action: PermissionAction.CREATE }
      }
    ]
  },

  {
    id: 'enrollments',
    label: 'Enrollments',
    icon: <Work />,
    path: '/enrollments',
    badge: 12,
    children: [
      {
        id: 'enrollment-status',
        label: 'Enrollment Status',
        icon: <Work />,
        path: '/enrollments/status',
        requiredPermission: { resource: PermissionResource.ENROLLMENTS, action: PermissionAction.READ }
      },
      {
        id: 'carrier-exports',
        label: 'Carrier Exports',
        icon: <Description />,
        path: '/enrollments/exports',
        requiredRoles: [SystemRole.BROKER_ADMIN, SystemRole.BROKER_USER]
      }
    ]
  },

  // Reports Section
  {
    id: 'reports',
    label: 'Reports & Analytics',
    icon: <Assessment />,
    path: '/reports',
    requiredPermission: { resource: PermissionResource.REPORTS, action: PermissionAction.READ },
    children: [
      {
        id: 'enrollment-reports',
        label: 'Enrollment Reports',
        icon: <InsertChart />,
        path: '/reports/enrollment',
        requiredPermission: { resource: PermissionResource.REPORTS, action: PermissionAction.READ }
      },
      {
        id: 'census-reports',
        label: 'Census Reports',
        icon: <People />,
        path: '/reports/census',
        requiredRoles: [SystemRole.BROKER_ADMIN, SystemRole.EMPLOYER_ADMIN]
      }
    ],
    dividerAfter: true
  },

  // Employee Self-Service Section
  {
    id: 'my-profile',
    label: 'My Profile',
    icon: <Person />,
    path: '/profile',
    requiredRole: SystemRole.EMPLOYEE
  },

  {
    id: 'my-benefits',
    label: 'My Benefits',
    icon: <Assignment />,
    path: '/my-benefits',
    requiredRole: SystemRole.EMPLOYEE
  },

  // Settings Section
  {
    id: 'settings',
    label: 'Settings',
    icon: <Settings />,
    path: '/settings',
    requiredPermission: { resource: PermissionResource.SETTINGS, action: PermissionAction.READ },
    children: [
      {
        id: 'organization-settings',
        label: 'Organization Settings',
        icon: <Settings />,
        path: '/settings/organization',
        requiredRoles: [SystemRole.SUPER_ADMIN, SystemRole.BROKER_ADMIN, SystemRole.EMPLOYER_ADMIN]
      },
      {
        id: 'user-settings',
        label: 'User Preferences',
        icon: <AccountCircle />,
        path: '/settings/user'
      }
    ]
  }
];

interface RoleBasedNavigationProps {
  open: boolean;
  onClose: () => void;
}

export const RoleBasedNavigation: React.FC<RoleBasedNavigationProps> = ({ open, onClose }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { filterMenuItems, user, userRole } = useRBAC();
  const { logout } = useAuth();
  const [expandedItems, setExpandedItems] = React.useState<string[]>(['employers', 'employees', 'plans']);
  const [userMenuAnchor, setUserMenuAnchor] = React.useState<null | HTMLElement>(null);

  // Filter navigation items based on user permissions
  const filteredNavItems = useMemo(() => {
    return filterMenuItems(NAVIGATION_ITEMS as NavigationMenuItem[]) as NavigationItem[];
  }, [filterMenuItems]);

  const handleItemClick = (path: string) => {
    navigate(path);
    onClose();
  };

  const handleExpandClick = (itemId: string) => {
    setExpandedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  const handleLogout = () => {
    handleUserMenuClose();
    logout();
    navigate('/login');
  };

  const getRoleDisplayInfo = (role: SystemRole | string | null) => {
    if (!role) return { color: 'default' as const, label: 'Unknown' };

    const roleConfig: Record<string, { color: 'primary' | 'secondary' | 'success' | 'warning' | 'error', label: string }> = {
      [SystemRole.SUPER_ADMIN]: { color: 'error', label: 'Super Admin' },
      [SystemRole.BROKER_ADMIN]: { color: 'primary', label: 'Broker Admin' },
      [SystemRole.BROKER_USER]: { color: 'primary', label: 'Broker User' },
      [SystemRole.EMPLOYER_ADMIN]: { color: 'secondary', label: 'Employer Admin' },
      [SystemRole.EMPLOYER_HR]: { color: 'secondary', label: 'HR Manager' },
      [SystemRole.EMPLOYEE]: { color: 'success', label: 'Employee' },
      [SystemRole.CARRIER_ADMIN]: { color: 'warning', label: 'Carrier Admin' }
    };

    return roleConfig[role] || { color: 'default' as const, label: role };
  };

  const roleInfo = getRoleDisplayInfo(userRole);

  const renderNavigationItem = (item: NavigationItem, depth = 0) => {
    const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/');
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.id);

    return (
      <PermissionGate
        key={item.id}
        resource={item.requiredPermission?.resource}
        action={item.requiredPermission?.action}
        role={item.requiredRole}
        roles={item.requiredRoles}
      >
        <ListItem disablePadding sx={{ display: 'block' }}>
          <ListItemButton
            onClick={() => hasChildren ? handleExpandClick(item.id) : handleItemClick(item.path)}
            sx={{
              minHeight: 48,
              px: 2.5,
              pl: depth * 2 + 2.5,
              backgroundColor: isActive ? 'action.selected' : 'transparent',
              '&:hover': {
                backgroundColor: 'action.hover',
              },
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 0,
                mr: 3,
                justifyContent: 'center',
                color: isActive ? 'primary.main' : 'text.secondary',
              }}
            >
              {item.badge ? (
                <Badge badgeContent={item.badge} color="error">
                  {item.icon}
                </Badge>
              ) : (
                item.icon
              )}
            </ListItemIcon>
            <ListItemText
              primary={item.label}
              sx={{
                opacity: 1,
                '& .MuiListItemText-primary': {
                  fontSize: depth > 0 ? '0.875rem' : '1rem',
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? 'primary.main' : 'text.primary',
                },
              }}
            />
            {hasChildren && (
              isExpanded ? <ExpandLess /> : <ExpandMore />
            )}
          </ListItemButton>
          
          {hasChildren && (
            <Collapse in={isExpanded} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {item.children!.map(child => renderNavigationItem(child, depth + 1))}
              </List>
            </Collapse>
          )}
        </ListItem>
        
        {item.dividerAfter && <Divider sx={{ my: 1 }} />}
      </PermissionGate>
    );
  };

  return (
    <>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            HRIS - Group Benefits
          </Typography>
          
          {user && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <PermissionGate resource={PermissionResource.ENROLLMENTS} action={PermissionAction.READ}>
                <IconButton color="inherit">
                  <Badge badgeContent={3} color="error">
                    <NotificationsActive />
                  </Badge>
                </IconButton>
              </PermissionGate>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Avatar
                  src={user.photoURL}
                  sx={{ width: 32, height: 32, cursor: 'pointer' }}
                  onClick={handleUserMenuOpen}
                >
                  {user.displayName?.[0] || user.email[0]?.toUpperCase()}
                </Avatar>
                <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
                  <Typography variant="body2" sx={{ color: 'inherit', lineHeight: 1 }}>
                    {user.displayName || user.email}
                  </Typography>
                  <Chip 
                    label={roleInfo.label} 
                    size="small" 
                    color={roleInfo.color}
                    sx={{ height: 16, fontSize: '0.675rem' }}
                  />
                </Box>
              </Box>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* User Menu */}
      <Menu
        anchorEl={userMenuAnchor}
        open={Boolean(userMenuAnchor)}
        onClose={handleUserMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={() => { handleUserMenuClose(); navigate('/profile'); }}>
          <ListItemIcon><AccountCircle /></ListItemIcon>
          <ListItemText>Profile</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { handleUserMenuClose(); navigate('/settings/user'); }}>
          <ListItemIcon><Settings /></ListItemIcon>
          <ListItemText>Settings</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>
          <ListItemIcon><ExitToApp /></ListItemIcon>
          <ListItemText>Sign Out</ListItemText>
        </MenuItem>
      </Menu>

      {/* Sidebar */}
      <Drawer
        variant="temporary"
        open={open}
        onClose={onClose}
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            mt: 8, // Account for AppBar height
          },
        }}
      >
        <Box sx={{ overflow: 'auto', height: '100%' }}>
          <List sx={{ pt: 1 }}>
            {filteredNavItems.map(item => renderNavigationItem(item))}
          </List>
        </Box>
      </Drawer>
    </>
  );
};

export default RoleBasedNavigation;