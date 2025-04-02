// src/services/api.ts
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Base URL for the API
const API_URL = 'http://10.0.2.2:8000'; // Use this for Android emulator
// const API_URL = 'http://localhost:8000'; // Use this for iOS simulator

// Create an axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token to requests
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle 401 Unauthorized responses (token expired)
    if (error.response && error.response.status === 401) {
      try {
        // Try to refresh token
        const refreshToken = await AsyncStorage.getItem('refreshToken');
        if (!refreshToken) {
          // No refresh token, force logout
          await AsyncStorage.removeItem('token');
          await AsyncStorage.removeItem('refreshToken');
          // Here you might want to redirect to login
          return Promise.reject(error);
        }

        // Call token refresh endpoint
        const response = await axios.post(
          `${API_URL}/auth/refresh`,
          {},
          {
            headers: {
              Authorization: `Bearer ${refreshToken}`,
            },
          }
        );

        // Store new tokens
        await AsyncStorage.setItem('token', response.data.access_token);
        await AsyncStorage.setItem('refreshToken', response.data.refresh_token);

        // Retry the original request with new token
        error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
        return axios(error.config);
      } catch (refreshError) {
        // Refresh failed, force logout
        await AsyncStorage.removeItem('token');
        await AsyncStorage.removeItem('refreshToken');
        // Here you might want to redirect to login
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  }
);

// Authentication API services
export const authService = {
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await axios.post(`${API_URL}/auth/token`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    // Store tokens
    await AsyncStorage.setItem('token', response.data.access_token);
    await AsyncStorage.setItem('refreshToken', response.data.refresh_token);
    
    return response.data;
  },

  register: async (userData: any) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      // Clear tokens regardless of API call success
      await AsyncStorage.removeItem('token');
      await AsyncStorage.removeItem('refreshToken');
    }
  },

  isAuthenticated: async () => {
    const token = await AsyncStorage.getItem('token');
    return !!token;
  },
};

// Gift Card API services
export const giftCardService = {
  getAllGiftCards: async (userId: string, page = 1, search = '') => {
    const response = await api.get(`/users/${userId}/gift-cards`, {
      params: { page, search },
    });
    return response.data;
  },

  getGiftCard: async (cardId: string) => {
    const response = await api.get(`/gift-cards/${cardId}`);
    return response.data;
  },

  createGiftCard: async (giftCardData: FormData) => {
    const response = await api.post('/gift-cards', giftCardData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  updateGiftCardBalance: async (cardId: string, balance: number) => {
    const response = await api.put(`/gift-cards/${cardId}/balance`, { balance });
    return response.data;
  },

  getGiftCardImage: async (cardId: string, imageType: 'front' | 'back') => {
    return `${API_URL}/gift-cards/${cardId}/images/${imageType}`;
  },
};

// Vendor API services
export const vendorService = {
  getAllVendors: async (page = 1, search = '') => {
    const response = await api.get('/vendors', {
      params: { page, search },
    });
    return response.data;
  },

  getVendor: async (vendorId: string) => {
    const response = await api.get(`/vendors/${vendorId}`);
    return response.data;
  },

  getVendorLogo: (vendorId: string) => {
    return `${API_URL}/vendors/${vendorId}/logo`;
  },
};

// User API services
export const userService = {
  getUserProfile: async () => {
    const response = await api.get('/users/me');
    return response.data;
  },

  updateUserProfile: async (userData: any) => {
    const response = await api.put('/users/me', userData);
    return response.data;
  },

  changePassword: async (
    currentPassword: string,
    newPassword: string
  ) => {
    const response = await api.put('/users/me/password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};

export default api;