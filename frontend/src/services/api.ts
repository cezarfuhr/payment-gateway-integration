import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Payment API
export const paymentAPI = {
  create: (data: any) => api.post('/payments/', data),
  list: (params?: any) => api.get('/payments/', { params }),
  get: (id: string) => api.get(`/payments/${id}`),
  sync: (id: string) => api.post(`/payments/${id}/sync`),
  refund: (data: any) => api.post('/payments/refunds', data),
  cancel: (id: string) => api.post(`/payments/${id}/cancel`),
};

// Report API
export const reportAPI = {
  create: (data: any) => api.post('/reports/', data),
  list: (params?: any) => api.get('/reports/', { params }),
  get: (id: string) => api.get(`/reports/${id}`),
  dashboard: () => api.get('/reports/dashboard/stats'),
};

// Health check
export const healthCheck = () => axios.get(`${API_URL}/health`);
