import { buildUrl, getAuthHeaders } from './config';
import { apiFetch } from './auth';

export const cartAPI = {
  getCart: async () => {
    const res = await apiFetch(buildUrl('/cart/'), { headers: getAuthHeaders() });
    return res.json();
  },

  addToCart: async (productId, quantity = 1) => {
    const res = await apiFetch(buildUrl('/cart/add/'), {
      method:  'POST',
      headers: getAuthHeaders(),
      body:    JSON.stringify({ product_id: productId, quantity }),
    });
    return res.json();
  },

  updateItem: async (itemId, quantity) => {
    const res = await apiFetch(buildUrl(`/cart/items/${itemId}/`), {
      method:  'PATCH',
      headers: getAuthHeaders(),
      body:    JSON.stringify({ quantity }),
    });
    return res.json();
  },

  removeItem: async (itemId) => {
    const res = await apiFetch(buildUrl(`/cart/items/${itemId}/`), {
      method:  'DELETE',
      headers: getAuthHeaders(),
    });
    return res.json();
  },

  clearCart: async () => {
    const res = await apiFetch(buildUrl('/cart/clear/'), {
      method:  'DELETE',
      headers: getAuthHeaders(),
    });
    return res.json();
  },
};
