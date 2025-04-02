// src/context/AuthContext.tsx
import React, { createContext, useState, useEffect, useContext } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authService, userService } from '../services/api';

interface User {
  user_id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

interface AuthContextData {
  user: User | null;
  isLoading: boolean;
  isSignedIn: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signUp: (userData: any) => Promise<void>;
  signOut: () => Promise<void>;
  loadUserProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextData>({} as AuthContextData);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSignedIn, setIsSignedIn] = useState(false);

  // Check if user is already signed in
  useEffect(() => {
    const bootstrapAsync = async () => {
      try {
        const isAuthenticated = await authService.isAuthenticated();
        
        if (isAuthenticated) {
          try {
            await loadUserProfile();
            setIsSignedIn(true);
          } catch (error) {
            // Token may be expired or invalid
            await authService.logout();
            setIsSignedIn(false);
          }
        }
      } catch (error) {
        console.error('Bootstrap error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    bootstrapAsync();
  }, []);

  const loadUserProfile = async () => {
    try {
      const userData = await userService.getUserProfile();
      setUser(userData);
    } catch (error) {
      console.error('Error loading user profile:', error);
      throw error;
    }
  };

  const signIn = async (username: string, password: string) => {
    try {
      setIsLoading(true);
      await authService.login(username, password);
      await loadUserProfile();
      setIsSignedIn(true);
    } catch (error) {
      console.error('Sign in error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const signUp = async (userData: any) => {
    try {
      setIsLoading(true);
      await authService.register(userData);
      // After registration, sign in automatically
      await signIn(userData.username, userData.password);
    } catch (error) {
      console.error('Sign up error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const signOut = async () => {
    try {
      setIsLoading(true);
      await authService.logout();
      setUser(null);
      setIsSignedIn(false);
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isSignedIn,
        signIn,
        signUp,
        signOut,
        loadUserProfile
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;