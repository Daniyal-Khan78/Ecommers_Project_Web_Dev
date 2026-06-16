import { buildUrl, getAuthHeaders } from './config';
import { apiFetch } from './auth';

export const ordersAPI = {
  placeOrder: async (data) => {
    const res = await apiFetch(buildUrl('/orders/create/'), {
      method:  'POST',
      headers: getAuthHeaders(),
      body:    JSON.stringify(data),
    });
    return res.json();
  },

  getOrders: async (params = {}) => {
    const qs  = params.status ? `?status=${params.status}` : '';
    const res = await apiFetch(buildUrl(`/orders/${qs}`), { headers: getAuthHeaders() });
    return res.json();
  },

  getOrder: async (id) => {
    const res = await apiFetch(buildUrl(`/orders/${id}/`), { headers: getAuthHeaders() });
    return res.json();
  },

  cancelOrder: async (id) => {
    const res = await apiFetch(buildUrl(`/orders/${id}/cancel/`), {
      method:  'POST',
      headers: getAuthHeaders(),
    });
    return res.json();
  },

  // Admin
  getAllOrders: async (params = {}) => {
    const qs  = params.status ? `?status=${params.status}` : '';
    const res = await apiFetch(buildUrl(`/orders/admin/${qs}`), { headers: getAuthHeaders() });
    return res.json();
  },

  updateOrderStatus: async (id, status) => {
    const res = await apiFetch(buildUrl(`/orders/admin/${id}/`), {
      method:  'PATCH',
      headers: getAuthHeaders(),
      body:    JSON.stringify({ status }),
    });
    return res.json();
  },

  getAnalytics: async () => {
    const res = await apiFetch(buildUrl('/orders/admin/analytics/'), {
      headers: getAuthHeaders(),
    });
    return res.json();
  },
};
