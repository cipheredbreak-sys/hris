import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Avatar,
  Chip,
  IconButton,
  Alert,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  TrendingUp,
  People,
  Business,
  Assignment,
  Notifications,
  ChevronRight,
  Warning,
  CheckCircle,
  Schedule,
  Assessment,
  FileDownload,
  Add,
  Settings,
  AdminPanelSettings
} from '@mui/icons-material';
import { useRBAC } from '../../contexts/RBACContext';
import { PermissionGate } from '../rbac/PermissionGate';
import { SystemRole, PermissionResource, PermissionAction } from '../../types/rbac';

interface DashboardCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  icon: React.ReactElement;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  action?: {
    label: string;
    onClick: () => void;
  };
}

const DashboardCard: React.FC<DashboardCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon,
  color = 'primary',
  action
}) => {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h4" component="div" sx={{ mb: 1 }}>
              {value}
            </Typography>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary">
                {subtitle}
              </Typography>
            )}
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUp 
                  sx={{ 
                    fontSize: 16, 
                    mr: 0.5, 
                    color: trend.isPositive ? 'success.main' : 'error.main',
                    transform: trend.isPositive ? 'none' : 'rotate(180deg)'
                  }} 
                />
                <Typography 
                  variant="body2" 
                  sx={{ color: trend.isPositive ? 'success.main' : 'error.main' }}
                >
                  {Math.abs(trend.value)}% from last month
                </Typography>
              </Box>
            )}
          </Box>
          <Avatar sx={{ bgcolor: `${color}.main` }}>
            {icon}
          </Avatar>
        </Box>
        {action && (
          <Box sx={{ mt: 2 }}>
            <Button 
              size="small" 
              onClick={action.onClick}
              endIcon={<ChevronRight />}
            >
              {action.label}
            </Button>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

// Super Admin Dashboard
const SuperAdminDashboard: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Administration
      </Typography>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Total Organizations"
            value={47}
            subtitle="Brokers, Employers, Carriers"
            icon={<Business />}
            color="primary"
            trend={{ value: 8, isPositive: true }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Active Users"
            value={1253}
            subtitle="Across all organizations"
            icon={<People />}
            color="success"
            trend={{ value: 12, isPositive: true }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="System Health"
            value="98.7%"
            subtitle="Uptime last 30 days"
            icon={<CheckCircle />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Active Enrollments"
            value={15847}
            subtitle="Current enrollment period"
            icon={<Assignment />}
            color="secondary"
            trend={{ value: 23, isPositive: true }}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent System Activity
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon><AdminPanelSettings color="primary" /></ListItemIcon>
                  <ListItemText 
                    primary="New broker organization created"
                    secondary="Acme Benefits Partners - 2 hours ago"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Warning color="warning" /></ListItemIcon>
                  <ListItemText 
                    primary="High API usage detected"
                    secondary="Boston Insurance Co - 3 hours ago"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                  <ListItemText 
                    primary="System backup completed"
                    secondary="Daily backup - 4 hours ago"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Button variant="contained" startIcon={<Add />}>
                  Create Organization
                </Button>
                <Button variant="outlined" startIcon={<People />}>
                  Manage Users
                </Button>
                <Button variant="outlined" startIcon={<Assessment />}>
                  System Reports
                </Button>
                <Button variant="outlined" startIcon={<Settings />}>
                  System Settings
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

// Broker Dashboard
const BrokerDashboard: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Broker Console
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        <strong>Enrollment Period Active:</strong> Q1 2024 enrollments are currently open. 
        12 employers have pending submissions.
      </Alert>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Active Employers"
            value={23}
            subtitle="Under management"
            icon={<Business />}
            color="primary"
            action={{ label: "View All", onClick: () => console.log('Navigate to employers') }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Total Employees"
            value={1847}
            subtitle="Across all employers"
            icon={<People />}
            color="secondary"
            trend={{ value: 5, isPositive: true }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Enrollment Progress"
            value="73%"
            subtitle="Current period completion"
            icon={<Assignment />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Pending Exports"
            value={5}
            subtitle="Ready for carrier submission"
            icon={<FileDownload />}
            color="error"
            action={{ label: "Process", onClick: () => console.log('Navigate to exports') }}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Enrollment Status by Employer
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">TechCorp Inc.</Typography>
                  <Typography variant="body2">45/50 employees</Typography>
                </Box>
                <LinearProgress variant="determinate" value={90} sx={{ mb: 2 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Metro Manufacturing</Typography>
                  <Typography variant="body2">28/35 employees</Typography>
                </Box>
                <LinearProgress variant="determinate" value={80} sx={{ mb: 2 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Green Energy Solutions</Typography>
                  <Typography variant="body2">12/25 employees</Typography>
                </Box>
                <LinearProgress variant="determinate" value={48} color="warning" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" sx={{ fontSize: 20 }} /></ListItemIcon>
                  <ListItemText 
                    primary="Export completed"
                    secondary="Aetna Medical - TechCorp"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Schedule color="warning" sx={{ fontSize: 20 }} /></ListItemIcon>
                  <ListItemText 
                    primary="Pending approval"
                    secondary="New employer setup"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon><Assignment color="info" sx={{ fontSize: 20 }} /></ListItemIcon>
                  <ListItemText 
                    primary="Enrollment started"
                    secondary="Metro Manufacturing"
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

// Employer Dashboard
const EmployerDashboard: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Employer Portal
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Total Employees"
            value={87}
            subtitle="Eligible for benefits"
            icon={<People />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Enrolled"
            value={73}
            subtitle="84% completion rate"
            icon={<CheckCircle />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Pending"
            value={14}
            subtitle="Awaiting enrollment"
            icon={<Schedule />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <DashboardCard
            title="Available Plans"
            value={12}
            subtitle="Medical, Dental, Vision"
            icon={<Assignment />}
            color="secondary"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Enrollment Progress by Department
              </Typography>
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Engineering (32 employees)</Typography>
                  <Typography variant="body2">100% enrolled</Typography>
                </Box>
                <LinearProgress variant="determinate" value={100} color="success" sx={{ mb: 2 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Sales (25 employees)</Typography>
                  <Typography variant="body2">88% enrolled</Typography>
                </Box>
                <LinearProgress variant="determinate" value={88} sx={{ mb: 2 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Operations (30 employees)</Typography>
                  <Typography variant="body2">70% enrolled</Typography>
                </Box>
                <LinearProgress variant="determinate" value={70} color="warning" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Button variant="contained" startIcon={<Add />}>
                  Add Employee
                </Button>
                <Button variant="outlined" startIcon={<FileDownload />}>
                  Download Census
                </Button>
                <Button variant="outlined" startIcon={<Assessment />}>
                  Enrollment Report
                </Button>
                <Button variant="outlined" startIcon={<Notifications />}>
                  Send Reminders
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

// Employee Dashboard
const EmployeeDashboard: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        My Benefits
      </Typography>
      
      <Alert severity="success" sx={{ mb: 3 }}>
        <strong>Enrollment Complete!</strong> Your benefit selections have been submitted successfully.
      </Alert>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                My Current Elections
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                  <ListItemText 
                    primary="Aetna PPO Medical"
                    secondary="Employee + Family • $245.50/month"
                  />
                  <Chip label="Active" color="success" size="small" />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                  <ListItemText 
                    primary="Delta Dental PPO"
                    secondary="Employee + Family • $52.75/month"
                  />
                  <Chip label="Active" color="success" size="small" />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemIcon><CheckCircle color="success" /></ListItemIcon>
                  <ListItemText 
                    primary="Vision Service Plan"
                    secondary="Employee + Family • $18.20/month"
                  />
                  <Chip label="Active" color="success" size="small" />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Monthly Summary
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Total Premium
                </Typography>
                <Typography variant="h4">
                  $316.45
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  per month
                </Typography>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Your employer contributes 80% of the premium cost
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Available Actions
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button variant="outlined" startIcon={<FileDownload />}>
              Download Summary
            </Button>
            <Button variant="outlined" startIcon={<People />}>
              Update Dependents
            </Button>
            <Button variant="outlined" startIcon={<Settings />}>
              Beneficiaries
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

// Main Role-Based Dashboard Component
export const RoleBasedDashboard: React.FC = () => {
  const { userRole, user } = useRBAC();

  if (!user) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">
          Please log in to view your dashboard.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {userRole === SystemRole.SUPER_ADMIN && (
        <SuperAdminDashboard />
      )}

      {userRole === SystemRole.BROKER_ADMIN && (
        <BrokerDashboard />
      )}

      {userRole === SystemRole.BROKER_USER && (
        <BrokerDashboard />
      )}

      {userRole === SystemRole.EMPLOYER_ADMIN && (
        <EmployerDashboard />
      )}

      {userRole === SystemRole.EMPLOYER_HR && (
        <EmployerDashboard />
      )}

      {userRole === SystemRole.EMPLOYEE && (
        <EmployeeDashboard />
      )}

      {/* Fallback for unrecognized roles */}
      {(!userRole || !Object.values(SystemRole).includes(userRole as SystemRole)) && (
        <Alert severity="info">
          <Typography variant="h6" gutterBottom>
            Welcome to HRIS Group Benefits!
          </Typography>
          <Typography>
            Your account role is not fully configured. 
            Please contact your administrator to set up your dashboard access.
          </Typography>
        </Alert>
      )}
    </Box>
  );
};

export default RoleBasedDashboard;