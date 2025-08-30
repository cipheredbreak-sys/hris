import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
}

export interface SignupData {
  firstName: string;
  lastName: string;
  email: string;
  company: string;
  password: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (data: SignupData) => Promise<boolean>;
  socialLogin: (provider: 'google' | 'microsoft') => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing authentication on app load
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        if (token) {
          // For demo purposes, skip backend validation if it fails
          // In production, you'd validate with the backend
          console.log('Found token in localStorage, assuming valid for demo');
          
          // For demo purposes, create a mock user when token exists
          // In production, you'd fetch user data from the backend
          const mockUser = {
            id: '1',
            email: 'demo@example.com',
            firstName: 'Demo',
            lastName: 'User',
            role: 'broker_admin' // Use proper RBAC role
          };
          setUser(mockUser);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('token');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      // Demo login - accept demo credentials for different personas
      const testUsers = {
        'superadmin@hris.com': {
          id: '1',
          email: 'superadmin@hris.com',
          firstName: 'Sarah',
          lastName: 'Administrator',
          role: 'super_admin'
        },
        'broker.admin@brokerage.com': {
          id: '2',
          email: 'broker.admin@brokerage.com',
          firstName: 'Mike',
          lastName: 'Broker',
          role: 'broker_admin'
        },
        'broker.user@brokerage.com': {
          id: '3',
          email: 'broker.user@brokerage.com',
          firstName: 'Lisa',
          lastName: 'Sales',
          role: 'broker_user'
        },
        'employer.admin@company.com': {
          id: '4',
          email: 'employer.admin@company.com',
          firstName: 'John',
          lastName: 'Manager',
          role: 'employer_admin'
        },
        'hr@company.com': {
          id: '5',
          email: 'hr@company.com',
          firstName: 'Emma',
          lastName: 'HRDirector',
          role: 'employer_hr'
        },
        'employee@company.com': {
          id: '6',
          email: 'employee@company.com',
          firstName: 'David',
          lastName: 'Employee',
          role: 'employee'
        },
        'demo@example.com': {
          id: '7',
          email: 'demo@example.com',
          firstName: 'Demo',
          lastName: 'User',
          role: 'broker_admin'
        }
      };

      // Check for test user credentials (password is always "demo123")
      if (testUsers[email as keyof typeof testUsers] && password === 'demo123') {
        const mockToken = 'demo-token-' + Date.now();
        const mockUser = testUsers[email as keyof typeof testUsers];
        
        localStorage.setItem('token', mockToken);
        setUser(mockUser);
        return true;
      }

      // Try backend authentication as fallback
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8089/api'}/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const signup = async (data: SignupData): Promise<boolean> => {
    try {
      // Demo signup - create mock user
      const mockToken = 'demo-signup-token-' + Date.now();
      const mockUser = {
        id: Date.now().toString(),
        email: data.email,
        firstName: data.firstName,
        lastName: data.lastName,
        role: 'broker_admin' // Use proper RBAC role
      };
      
      localStorage.setItem('token', mockToken);
      setUser(mockUser);
      return true;

      // Uncomment below for real backend integration:
      /*
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8089/api'}/auth/signup/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        const responseData = await response.json();
        localStorage.setItem('token', responseData.access_token);
        setUser(responseData.user);
        return true;
      }
      return false;
      */
    } catch (error) {
      console.error('Signup failed:', error);
      return false;
    }
  };

  const socialLogin = async (provider: 'google' | 'microsoft'): Promise<boolean> => {
    try {
      // Demo social login
      const mockToken = `demo-${provider}-token-` + Date.now();
      const mockUser = {
        id: Date.now().toString(),
        email: `demo@${provider}.com`,
        firstName: provider === 'google' ? 'Google' : 'Microsoft',
        lastName: 'User',
        role: 'broker_admin' // Use proper RBAC role
      };
      
      localStorage.setItem('token', mockToken);
      setUser(mockUser);
      return true;

      // Uncomment below for real social login integration:
      /*
      window.location.href = `${process.env.REACT_APP_API_URL || 'http://localhost:8089/api'}/auth/${provider}/`;
      return true; // The redirect will handle the rest
      */
    } catch (error) {
      console.error(`${provider} login failed:`, error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    signup,
    socialLogin,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};