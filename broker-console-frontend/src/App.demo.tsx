import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Button, 
  Alert, 
  Paper, 
  Grid, 
  Chip,
  Card,
  CardContent,
  AppBar,
  Toolbar,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Avatar,
  Menu,
  MenuItem
} from '@mui/material';
import { 
  Dashboard, 
  Person, 
  AdminPanelSettings, 
  Business, 
  Work,
  Menu as MenuIcon,
  AccountCircle,
  ExitToApp,
  People,
  Assignment
} from '@mui/icons-material';

// Theme colors
const THEME_COLORS = {
  primary: '#00A3A1',
  primaryDark: '#006B6D',
  secondary: '#FF6B35',
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    600: '#4B5563',
    900: '#1F2937'
  }
};

// Demo users for testing RBAC
interface DemoUser {
  uid: string;
  email: string;
  displayName: string;
  role: string;
  organizationId?: string;
}

const DEMO_USERS: Record<string, DemoUser> = {
  'super@admin.com': {
    uid: '1',
    email: 'super@admin.com',
    displayName: 'Super Admin',
    role: 'super_admin'
  },
  'broker@admin.com': {
    uid: '2',
    email: 'broker@admin.com',
    displayName: 'John Smith',
    role: 'broker_admin',
    organizationId: 'broker-1'
  },
  'broker@user.com': {
    uid: '3',
    email: 'broker@user.com',
    displayName: 'Jane Doe',
    role: 'broker_user',
    organizationId: 'broker-1'
  },
  'employer@admin.com': {
    uid: '4',
    email: 'employer@admin.com',
    displayName: 'Mike Johnson',
    role: 'employer_admin',
    organizationId: 'employer-1'
  },
  'employee@test.com': {
    uid: '5',
    email: 'employee@test.com',
    displayName: 'Sarah Wilson',
    role: 'employee',
    organizationId: 'employer-1'
  }
};

const DEMO_USER_INFO: Record<string, { 
  role: string; 
  description: string; 
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error'; 
  icon: React.ReactElement;
  features: string[];
}> = {
  'super@admin.com': {
    role: 'Super Admin',
    description: 'Full system access, manage all organizations',
    color: 'error',
    icon: <AdminPanelSettings />,
    features: ['Manage all organizations', 'User management', 'System settings']
  },
  'broker@admin.com': {
    role: 'Broker Admin', 
    description: 'Manage employers, employees, and benefit plans',
    color: 'primary',
    icon: <Business />,
    features: ['Create employers', 'Manage plans', 'Export data']
  },
  'broker@user.com': {
    role: 'Broker User',
    description: 'View and update employer/employee information',
    color: 'primary',
    icon: <Business />,
    features: ['View employers', 'Update employees', 'Basic reports']
  },
  'employer@admin.com': {
    role: 'Employer Admin',
    description: 'Manage company employees and benefit elections',
    color: 'secondary',
    icon: <Work />,
    features: ['Manage employees', 'Configure benefits', 'Company reports']
  },
  'employee@test.com': {
    role: 'Employee',
    description: 'View and manage personal benefit elections',
    color: 'success',
    icon: <Person />,
    features: ['Personal profile', 'Benefit elections', 'Dependents']
  }
};

// Login Component
const LoginPage: React.FC<{ onLogin: (email: string) => boolean }> = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const success = onLogin(email);
    if (!success) {
      setError('Invalid credentials. Please try one of the demo accounts below.');
    }
  };

  const handleDemoLogin = (demoEmail: string) => {
    onLogin(demoEmail);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: THEME_COLORS.gray[50],
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <Box sx={{ width: '100%', maxWidth: 1200 }}>
        <Grid container spacing={4}>
          {/* Demo Users Panel */}
          <Grid item xs={12} lg={8}>
            <Paper elevation={2} sx={{ p: 4, borderRadius: 2 }}>
              <Typography 
                variant="h4" 
                sx={{ 
                  mb: 2, 
                  color: THEME_COLORS.primary, 
                  fontWeight: 600,
                  textAlign: 'center'
                }}
              >
                🎯 RBAC Demo - Role-Based Access Control
              </Typography>
              <Typography 
                variant="h6" 
                sx={{ 
                  mb: 3, 
                  color: THEME_COLORS.gray[600],
                  textAlign: 'center'
                }}
              >
                Click any card below to login as that user type
              </Typography>
              
              <Grid container spacing={3}>
                {Object.keys(DEMO_USERS).map((userEmail) => {
                  const userInfo = DEMO_USER_INFO[userEmail];
                  if (!userInfo) return null;
                  
                  return (
                    <Grid item xs={12} sm={6} lg={4} key={userEmail}>
                      <Card 
                        sx={{ 
                          cursor: 'pointer',
                          transition: 'all 0.3s ease',
                          height: '100%',
                          '&:hover': {
                            transform: 'translateY(-4px)',
                            boxShadow: 6
                          }
                        }}
                        onClick={() => handleDemoLogin(userEmail)}
                      >
                        <CardContent sx={{ p: 3 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                            <Box sx={{ color: THEME_COLORS.primary, mr: 1.5 }}>
                              {userInfo.icon}
                            </Box>
                            <Chip 
                              label={userInfo.role} 
                              color={userInfo.color} 
                              size="medium"
                              sx={{ fontWeight: 600 }}
                            />
                          </Box>
                          
                          <Typography 
                            variant="body1" 
                            sx={{ 
                              color: THEME_COLORS.gray[900], 
                              mb: 2,
                              fontWeight: 500
                            }}
                          >
                            {userInfo.description}
                          </Typography>
                          
                          <Box sx={{ mb: 2 }}>
                            <Typography 
                              variant="caption" 
                              sx={{ 
                                color: THEME_COLORS.gray[600],
                                display: 'block',
                                mb: 1,
                                fontWeight: 600
                              }}
                            >
                              Key Features:
                            </Typography>
                            {userInfo.features.map((feature, index) => (
                              <Typography 
                                key={index}
                                variant="caption" 
                                sx={{ 
                                  color: THEME_COLORS.gray[600],
                                  display: 'block',
                                  fontSize: '0.75rem'
                                }}
                              >
                                • {feature}
                              </Typography>
                            ))}
                          </Box>
                          
                          <Typography 
                            variant="caption" 
                            sx={{ 
                              color: THEME_COLORS.primary,
                              fontFamily: 'monospace',
                              backgroundColor: THEME_COLORS.gray[100],
                              px: 1,
                              py: 0.5,
                              borderRadius: 1,
                              display: 'inline-block'
                            }}
                          >
                            📧 {userEmail}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            </Paper>
          </Grid>

          {/* Login Form */}
          <Grid item xs={12} lg={4}>
            <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
              <Typography
                variant="h4"
                sx={{
                  color: THEME_COLORS.primary,
                  fontWeight: 600,
                  mb: 1,
                  textAlign: 'center'
                }}
              >
                Welcome Back
              </Typography>
              <Typography 
                variant="body1" 
                sx={{ 
                  color: THEME_COLORS.gray[600],
                  textAlign: 'center',
                  mb: 3 
                }}
              >
                Sign in to your HRIS account
              </Typography>

              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              <Box component="form" onSubmit={handleSubmit}>
                <input
                  type="email"
                  placeholder="Email Address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '12px',
                    marginBottom: '16px',
                    border: '1px solid #D1D5DB',
                    borderRadius: '4px',
                    fontSize: '16px'
                  }}
                />

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  sx={{
                    py: 1.5,
                    backgroundColor: THEME_COLORS.primary,
                    '&:hover': {
                      backgroundColor: THEME_COLORS.primaryDark,
                    },
                    fontWeight: 600,
                    mb: 2,
                  }}
                >
                  Sign In
                </Button>
              </Box>

              <Box sx={{ mt: 3, p: 2, backgroundColor: THEME_COLORS.gray[100], borderRadius: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                  💡 Quick Test:
                </Typography>
                <Typography variant="body2" sx={{ color: THEME_COLORS.gray[600] }}>
                  Click any role card above to instantly login and explore that user's experience!
                </Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

// Dashboard Component
const DashboardPage: React.FC<{ user: DemoUser; onLogout: () => void }> = ({ user, onLogout }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);

  const userInfo = DEMO_USER_INFO[user.email];
  
  const getMenuItems = () => {
    const baseItems = [
      { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' }
    ];

    switch (user.role) {
      case 'super_admin':
        return [
          ...baseItems,
          { text: 'System Admin', icon: <AdminPanelSettings />, path: '/admin' },
          { text: 'Organizations', icon: <Business />, path: '/organizations' },
          { text: 'All Users', icon: <People />, path: '/users' }
        ];
      case 'broker_admin':
      case 'broker_user':
        return [
          ...baseItems,
          { text: 'Employers', icon: <Business />, path: '/employers' },
          { text: 'Employees', icon: <People />, path: '/employees' },
          { text: 'Plans', icon: <Assignment />, path: '/plans' }
        ];
      case 'employer_admin':
        return [
          ...baseItems,
          { text: 'My Employees', icon: <People />, path: '/my-employees' },
          { text: 'Benefits Setup', icon: <Assignment />, path: '/benefits' }
        ];
      case 'employee':
        return [
          ...baseItems,
          { text: 'My Profile', icon: <Person />, path: '/profile' },
          { text: 'My Benefits', icon: <Assignment />, path: '/my-benefits' }
        ];
      default:
        return baseItems;
    }
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: 1201 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            onClick={() => setSidebarOpen(true)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            HRIS - Group Benefits
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip 
              label={userInfo?.role} 
              color={userInfo?.color}
              size="small"
            />
            <Avatar
              sx={{ 
                width: 32, 
                height: 32, 
                cursor: 'pointer',
                bgcolor: THEME_COLORS.secondary
              }}
              onClick={(e) => setUserMenuAnchor(e.currentTarget)}
            >
              {user.displayName[0]}
            </Avatar>
          </Box>
        </Toolbar>
      </AppBar>

      {/* User Menu */}
      <Menu
        anchorEl={userMenuAnchor}
        open={Boolean(userMenuAnchor)}
        onClose={() => setUserMenuAnchor(null)}
      >
        <MenuItem onClick={() => setUserMenuAnchor(null)}>
          <ListItemIcon><AccountCircle /></ListItemIcon>
          Profile
        </MenuItem>
        <MenuItem onClick={() => { setUserMenuAnchor(null); onLogout(); }}>
          <ListItemIcon><ExitToApp /></ListItemIcon>
          Sign Out
        </MenuItem>
      </Menu>

      {/* Sidebar */}
      <Drawer
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: 280,
            mt: 8
          }
        }}
      >
        <List>
          {getMenuItems().map((item, index) => (
            <ListItem key={index}>
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
        </List>
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: THEME_COLORS.gray[50],
          pt: 10,
          p: 3,
        }}
      >
        <Typography variant="h4" gutterBottom>
          {userInfo?.role} Dashboard
        </Typography>
        
        <Alert severity="success" sx={{ mb: 3 }}>
          <strong>🎉 RBAC Demo Active!</strong> You're logged in as {userInfo?.role}. 
          Notice how the navigation and content adapts to your role.
        </Alert>

        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Welcome, {user.displayName}!
              </Typography>
              <Typography variant="body1" paragraph>
                {userInfo?.description}
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Available Features:
                </Typography>
                {userInfo?.features.map((feature, index) => (
                  <Typography key={index} variant="body2" sx={{ mb: 0.5 }}>
                    ✓ {feature}
                  </Typography>
                ))}
              </Box>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                User Information
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Role:</strong> {user.role}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Email:</strong> {user.email}
              </Typography>
              {user.organizationId && (
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Organization:</strong> {user.organizationId}
                </Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

// Main App Component
function App() {
  const [currentUser, setCurrentUser] = useState<DemoUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = () => {
      const storedUser = localStorage.getItem('demo_user');
      if (storedUser) {
        try {
          const userData = JSON.parse(storedUser);
          setCurrentUser(userData);
        } catch (e) {
          localStorage.removeItem('demo_user');
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const handleLogin = (email: string) => {
    const user = DEMO_USERS[email];
    if (user) {
      setCurrentUser(user);
      localStorage.setItem('demo_user', JSON.stringify(user));
      return true;
    }
    return false;
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('demo_user');
  };

  if (loading) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: '100vh' 
        }}
      >
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            currentUser ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <LoginPage onLogin={handleLogin} />
            )
          } 
        />
        <Route 
          path="/dashboard" 
          element={
            currentUser ? (
              <DashboardPage user={currentUser} onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" replace />
            )
          } 
        />
        <Route 
          path="/" 
          element={
            currentUser ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <Navigate to="/login" replace />
            )
          } 
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;