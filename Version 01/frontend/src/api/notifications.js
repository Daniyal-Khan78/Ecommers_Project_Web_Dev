import { buildUrl, getAuthHeaders } from './config';
import { apiFetch } from './auth';

export const notificationsAPI = {
  getNotifications: async () => {
    const res = await apiFetch(buildUrl('/notifications/'), { headers: getAuthHeaders() });
    return res.json();
  },

  markAllRead: async () => {
    const res = await apiFetch(buildUrl('/notifications/read/'), {
      method:  'PUT',
      headers: getAuthHeaders(),
    });
    return res.json();
  },
};
