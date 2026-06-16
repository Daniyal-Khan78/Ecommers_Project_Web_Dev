import { buildUrl, getAuthHeaders, getAuthHeadersMultipart } from './config';

// Generic fetch wrapper that handles token refresh automatically.
// If a request returns 401 (token expired), refresh the access token and retry once.
async function apiFetch(url, options = {}) {
  let response = await fetch(url, options);

  if (response.status === 401) {
    // Try to refresh the access token
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      const refreshRes = await fetch(buildUrl('/auth/token/refresh/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (refreshRes.ok) {
        const data = await refreshRes.json();
        localStorage.setItem('access_token', data.access);
        // Retry original request with new token
        const newHeaders = { ...options.headers, Authorization: `Bearer ${data.access}` };
        response = await fetch(url, { ...options, headers: newHeaders });
      } else {
        // Refresh failed — token is completely expired, force logout
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
  }

  return response;
}

export const authAPI = {
  register: async (userData) => {
    const res = await fetch(buildUrl('/auth/register/'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });
    return res.json();
  },

  login: async (email, password) => {
    const res = await fetch(buildUrl('/auth/login/'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return res.json();
  },

  logout: async (refreshToken) => {
    const res = await apiFetch(buildUrl('/auth/logout/'), {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ refresh: refreshToken }),
    });
    return res.json();
  },

  getProfile: async () => {
    const res = await apiFetch(buildUrl('/auth/profile/'), {
      headers: getAuthHeaders(),
    });
    return res.json();
  },

  updateProfile: async (formData) => {
    // FormData handles both text fields and file uploads (profile image)
    const res = await apiFetch(buildUrl('/auth/profile/update/'), {
      method: 'PATCH',
      headers: getAuthHeadersMultipart(),
      body: formData,
    });
    return res.json();
  },

  changePassword: async (data) => {
    const res = await apiFetch(buildUrl('/auth/change-password/'), {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return res.json();
  },

  verifyEmail: async (token) => {
    const res = await fetch(buildUrl(`/auth/verify-email/${token}/`));
    return res.json();
  },

  resendVerification: async () => {
    const res = await apiFetch(buildUrl('/auth/resend-verification/'), {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return res.json();
  },

  // Admin
  getUsers: async () => {
    const res = await apiFetch(buildUrl('/auth/admin/users/'), {
      headers: getAuthHeaders(),
    });
    return res.json();
  },

  updateUser: async (userId, data) => {
    const res = await apiFetch(buildUrl(`/auth/admin/users/${userId}/`), {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return res.json();
  },
};

// Export apiFetch for use in other API modules
export { apiFetch };
