import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      window.location.href = '/login';
    } else if (error.code === 'ECONNREFUSED' || error.message.includes('ECONNREFUSED')) {
      // Handle backend connection errors
      console.warn('Backend server is not running. Using mock data for demonstration.');
    }
    return Promise.reject(error);
  }
);

export default api;
