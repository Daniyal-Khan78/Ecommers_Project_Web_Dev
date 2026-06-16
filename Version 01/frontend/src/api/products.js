import { buildUrl, getAuthHeaders, getAuthHeadersMultipart } from './config';
import { apiFetch } from './auth';

export const productsAPI = {
  // Build query string from a params object, ignoring empty values
  _buildQuery: (params = {}) => {
    const qs = Object.entries(params)
      .filter(([, v]) => v !== '' && v !== null && v !== undefined)
      .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
      .join('&');
    return qs ? `?${qs}` : '';
  },

  getProducts: async (params = {}) => {
    const qs  = productsAPI._buildQuery(params);
    const res = await fetch(buildUrl(`/products/${qs}`));
    return res.json();
  },

  getProduct: async (id) => {
    const res = await fetch(buildUrl(`/products/${id}/`));
    return res.json();
  },

  getFeatured: async () => {
    const res = await fetch(buildUrl('/products/featured/'));
    return res.json();
  },

  getRecommendations: async () => {
    const res = await apiFetch(buildUrl('/products/recommendations/'), {
      headers: getAuthHeaders(),
    });
    return res.json();
  },

  getCategories: async () => {
    const res = await fetch(buildUrl('/categories/'));
    return res.json();
  },

  getCategory: async (id) => {
    const res = await fetch(buildUrl(`/categories/${id}/`));
    return res.json();
  },

  // Admin
  createProduct: async (data) => {
    const res = await apiFetch(buildUrl('/products/'), {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return res.json();
  },

  updateProduct: async (id, data) => {
    const res = await apiFetch(buildUrl(`/products/${id}/`), {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return res.json();
  },

  deleteProduct: async (id) => {
    const res = await apiFetch(buildUrl(`/products/${id}/`), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    return res.ok ? { success: true } : res.json();
  },

  uploadImages: async (productId, formData) => {
    const res = await apiFetch(buildUrl(`/products/${productId}/images/`), {
      method: 'POST',
      headers: getAuthHeadersMultipart(),
      body: formData,
    });
    return res.json();
  },

  deleteImage: async (productId, imageId) => {
    const res = await apiFetch(buildUrl(`/products/${productId}/images/${imageId}/`), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    return res.ok ? { success: true } : res.json();
  },

  createCategory: async (data) => {
    const res = await apiFetch(buildUrl('/categories/'), {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return res.json();
  },

  updateCategory: async (id, data) => {
    const res = await apiFetch(buildUrl(`/categories/${id}/`), {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return res.json();
  },

  deleteCategory: async (id) => {
    const res = await apiFetch(buildUrl(`/categories/${id}/`), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    return res.ok ? { success: true } : res.json();
  },

  getAllProductsAdmin: async (params = {}) => {
    const qs  = productsAPI._buildQuery(params);
    const res = await apiFetch(buildUrl(`/products/admin/all/${qs}`), {
      headers: getAuthHeaders(),
    });
    return res.json();
  },
};
