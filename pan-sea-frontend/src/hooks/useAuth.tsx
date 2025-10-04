'use client';

import { useState, useEffect, useContext, createContext, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    
    // Only access localStorage and document if we're in the browser
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // Remove non-HttpOnly cookie (middleware relies on HttpOnly set by API routes)
      document.cookie = 'auth-token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT; samesite=lax';
    }
    
    router.push('/auth/login');
  }, [router]);

  useEffect(() => {
    // Only access localStorage if we're in the browser
    if (typeof window !== 'undefined') {
      // Check for stored auth data on mount
      const storedToken = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');

      if (storedToken && storedUser) {
        try {
          setToken(storedToken);
          setUser(JSON.parse(storedUser));
          
          // Set cookie for middleware
          document.cookie = `auth-token=${storedToken}; path=/; max-age=86400`; // 24 hours
        } catch (error) {
          console.error('Error parsing stored user data:', error);
          // Clear invalid data
          logout();
        }
      }
    }
    
    setIsLoading(false);
  }, [logout]);

  const login = useCallback((token: string, user: User) => {
    console.log('Auth: Logging in user:', user);
    setToken(token);
    setUser(user);
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    // Do NOT set auth cookie here; API routes set HttpOnly cookie
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
