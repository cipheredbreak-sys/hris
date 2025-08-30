import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme, Box } from '@mui/material';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { RBACProvider } from './contexts/RBACContext';
import { LoginForm } from './components/auth/LoginForm';
import { SignupForm } from './components/auth/SignupForm';
import { ProtectedRoute } from './components/rbac/ProtectedRoute';
import { RoleBasedNavigation } from './components/navigation/RoleBasedNavigation';
import { RoleBasedDashboard } from './components/dashboards/RoleBasedDashboard';

// UKG Theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#00A3A1',
      dark: '#006B6D',
      light: '#4DD0CE',
    },
    secondary: {
      main: '#FF6B35',
    },
    background: {
      default: '#F9FAFB',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
});

// Main App Layout Component  
const AppLayout: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();
  const [navigationOpen, setNavigationOpen] = useState(false);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh'
      }}>
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginForm />} />
        <Route path="/signup" element={<SignupForm />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <RBACProvider>
      <Box sx={{ display: 'flex' }}>
        <RoleBasedNavigation 
          open={navigationOpen} 
          onClose={() => setNavigationOpen(false)} 
        />
        <Box 
          component="main" 
          sx={{ 
            flexGrow: 1, 
            minHeight: '100vh',
            paddingTop: '64px', // Account for AppBar height
            width: '100%'
          }}
        >
          <Routes>
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <RoleBasedDashboard />
                </ProtectedRoute>
              } 
            />
            
            {/* Additional protected routes can be added here */}
            <Route 
              path="/employers" 
              element={
                <ProtectedRoute resource="employers" action="read">
                  <Box sx={{ p: 3 }}>
                    <h2>Employers Page - Coming Soon</h2>
                    <p>This page will show employer management functionality based on your role.</p>
                  </Box>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/employees" 
              element={
                <ProtectedRoute resource="employees" action="read">
                  <Box sx={{ p: 3 }}>
                    <h2>Employees Page - Coming Soon</h2>
                    <p>This page will show employee management functionality based on your role.</p>
                  </Box>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/plans" 
              element={
                <ProtectedRoute resource="plans" action="read">
                  <Box sx={{ p: 3 }}>
                    <h2>Plans Page - Coming Soon</h2>
                    <p>This page will show benefit plans management functionality based on your role.</p>
                  </Box>
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/admin" 
              element={
                <ProtectedRoute role="super_admin">
                  <Box sx={{ p: 3 }}>
                    <h2>Admin Page - Coming Soon</h2>
                    <p>This page is only accessible to Super Admins.</p>
                  </Box>
                </ProtectedRoute>
              } 
            />

            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Box>
      </Box>
    </RBACProvider>
  );
};

// Root App Component
function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <AppLayout />
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;