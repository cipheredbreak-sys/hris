import React from 'react';
import { Box, Typography, Button, Paper, Grid } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

const UKG_THEME = {
  primary: {
    main: '#00A3A1',
    tealDark: '#006B6D',
  },
  gray: {
    50: '#F9FAFB',
    600: '#4B5563',
  },
};

export const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: UKG_THEME.gray[50], p: 3 }}>
      <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box>
            <Typography variant="h4" sx={{ color: UKG_THEME.primary.tealDark, fontWeight: 600, mb: 1 }}>
              Broker Console Dashboard
            </Typography>
            <Typography variant="body1" sx={{ color: UKG_THEME.gray[600] }}>
              Welcome back, {user?.firstName} {user?.lastName}
            </Typography>
          </Box>
          <Button
            variant="outlined"
            onClick={logout}
            sx={{
              borderColor: UKG_THEME.primary.main,
              color: UKG_THEME.primary.main,
              '&:hover': {
                borderColor: UKG_THEME.primary.tealDark,
                color: UKG_THEME.primary.tealDark,
              },
            }}
          >
            Sign Out
          </Button>
        </Box>

        {/* Status Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" sx={{ color: UKG_THEME.primary.main, mb: 1 }}>
                ✅ Frontend
              </Typography>
              <Typography variant="body2">Port 3500</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" sx={{ color: UKG_THEME.primary.main, mb: 1 }}>
                ✅ Backend
              </Typography>
              <Typography variant="body2">Port 8089</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" sx={{ color: UKG_THEME.primary.main, mb: 1 }}>
                ✅ Authentication
              </Typography>
              <Typography variant="body2">Active Session</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" sx={{ color: UKG_THEME.primary.main, mb: 1 }}>
                ✅ Swagger
              </Typography>
              <Typography variant="body2">
                <a 
                  href="http://localhost:8089/swagger/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ color: UKG_THEME.primary.main, textDecoration: 'none' }}
                >
                  API Docs
                </a>
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* User Info */}
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ mb: 2, color: UKG_THEME.primary.tealDark }}>
            User Information
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" sx={{ color: UKG_THEME.gray[600], mb: 1 }}>
                <strong>Name:</strong> {user?.firstName} {user?.lastName}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" sx={{ color: UKG_THEME.gray[600], mb: 1 }}>
                <strong>Email:</strong> {user?.email}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" sx={{ color: UKG_THEME.gray[600], mb: 1 }}>
                <strong>Role:</strong> {user?.role}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" sx={{ color: UKG_THEME.gray[600], mb: 1 }}>
                <strong>User ID:</strong> {user?.id}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      </Box>
    </Box>
  );
};