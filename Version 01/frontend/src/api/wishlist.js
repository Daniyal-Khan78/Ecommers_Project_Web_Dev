import { buildUrl, getAuthHeaders } from './config';
import { apiFetch } from './auth';

export const wishlistAPI = {
  getWishlist: async () => {
    const res = await apiFetch(buildUrl('/wishlist/'), { headers: getAuthHeaders() });
    return res.json();
  },

  addToWishlist: async (productId) => {
    const res = await apiFetch(buildUrl('/wishlist/add/'), {
      method:  'POST',
      headers: getAuthHeaders(),
      body:    JSON.stringify({ product_id: productId }),
    });
    return res.json();
  },

  removeFromWishlist: async (itemId) => {
    const res = await apiFetch(buildUrl(`/wishlist/remove/${itemId}/`), {
      method:  'DELETE',
      headers: getAuthHeaders(),
    });
    return res.json();
  },

  checkWishlist: async (productId) => {
    const res = await apiFetch(buildUrl(`/wishlist/check/${productId}/`), {
      headers: getAuthHeaders(),
    });
    return res.json();
  },

  moveToCart: async (itemId) => {
    const res = await apiFetch(buildUrl(`/wishlist/${itemId}/move-to-cart/`), {
      method:  'POST',
      headers: getAuthHeaders(),
    });
    return res.json();
  },
};
