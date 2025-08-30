import React, { useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  IconButton,
  InputAdornment,
  Link,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Email as EmailIcon,
  Lock as LockIcon,
  Google as GoogleIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

const UKG_THEME = {
  primary: {
    main: '#00A3A1',
    teal: '#00A3A1',
    tealDark: '#006B6D',
    tealLight: '#4DD0CE',
  },
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
  },
};

export const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login, socialLogin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const success = await login(email, password);
      if (success) {
        // Force redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        setError('Invalid email or password. Please try again.');
      }
    } catch (err) {
      setError('Login failed. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSocialLogin = async (provider: 'google' | 'microsoft') => {
    setError('');
    setLoading(true);

    try {
      const success = await socialLogin(provider);
      if (success) {
        // Force redirect to dashboard
        window.location.href = '/dashboard';
      } else {
        setError(`${provider} authentication failed. Please try again.`);
      }
    } catch (err) {
      setError(`${provider} authentication failed. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: UKG_THEME.gray[50],
        padding: 2,
      }}
    >
      <Paper
        elevation={3}
        sx={{
          padding: 4,
          width: '100%',
          maxWidth: 400,
          borderRadius: 2,
        }}
      >
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Typography 
            variant="h4" 
            sx={{ 
              color: UKG_THEME.primary.tealDark,
              fontWeight: 600,
              mb: 1,
            }}
          >
            Welcome Back
          </Typography>
          <Typography 
            variant="body2" 
            sx={{ color: UKG_THEME.gray[600] }}
          >
            Sign in to your broker console
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Social Login Options */}
        <Box sx={{ mb: 3 }}>
          <Button
            fullWidth
            variant="outlined"
            size="large"
            onClick={() => handleSocialLogin('google')}
            disabled={loading}
            startIcon={<GoogleIcon />}
            sx={{
              mb: 2,
              borderColor: UKG_THEME.gray[300],
              color: UKG_THEME.gray[700],
              '&:hover': {
                borderColor: UKG_THEME.primary.main,
                backgroundColor: UKG_THEME.gray[50],
              },
            }}
          >
            Continue with Google
          </Button>

          <Button
            fullWidth
            variant="outlined"
            size="large"
            onClick={() => handleSocialLogin('microsoft')}
            disabled={loading}
            startIcon={
              <Box sx={{ width: 20, height: 20, backgroundColor: '#0078D4', borderRadius: '2px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography sx={{ color: 'white', fontSize: '12px', fontWeight: 'bold' }}>M</Typography>
              </Box>
            }
            sx={{
              mb: 2,
              borderColor: UKG_THEME.gray[300],
              color: UKG_THEME.gray[700],
              '&:hover': {
                borderColor: '#0078D4',
                backgroundColor: UKG_THEME.gray[50],
              },
            }}
          >
            Continue with Microsoft
          </Button>

          <Divider sx={{ my: 3 }}>
            <Typography variant="body2" sx={{ color: UKG_THEME.gray[500] }}>
              or continue with email
            </Typography>
          </Divider>
        </Box>

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            type="email"
            label="Email Address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            sx={{ mb: 3 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <EmailIcon sx={{ color: UKG_THEME.gray[400] }} />
                </InputAdornment>
              ),
            }}
          />

          <TextField
            fullWidth
            type={showPassword ? 'text' : 'password'}
            label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
            sx={{ mb: 3 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LockIcon sx={{ color: UKG_THEME.gray[400] }} />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={togglePasswordVisibility}
                    edge="end"
                    disabled={loading}
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={loading || !email || !password}
            sx={{
              backgroundColor: UKG_THEME.primary.main,
              '&:hover': {
                backgroundColor: UKG_THEME.primary.tealDark,
              },
              py: 1.5,
              mb: 2,
            }}
          >
            {loading ? (
              <CircularProgress size={24} sx={{ color: 'white' }} />
            ) : (
              'Sign In'
            )}
          </Button>
        </form>

        <Box sx={{ textAlign: 'center', mt: 3 }}>
          <Typography variant="body2" sx={{ color: UKG_THEME.gray[600] }}>
            Don't have an account?{' '}
            <Link 
              href="/signup" 
              sx={{ 
                color: UKG_THEME.primary.main,
                textDecoration: 'none',
                '&:hover': {
                  textDecoration: 'underline',
                },
              }}
            >
              Sign up
            </Link>
          </Typography>
        </Box>

      </Paper>
    </Box>
  );
};