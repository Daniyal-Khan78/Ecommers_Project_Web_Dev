import { buildUrl, getAuthHeaders } from './config';
import { apiFetch } from './auth';

export const paymentsAPI = {
  createIntent: async (orderId) => {
    const res = await apiFetch(buildUrl('/payments/create-intent/'), {
      method:  'POST',
      headers: getAuthHeaders(),
      body:    JSON.stringify({ order_id: orderId }),
    });
    return res.json();
  },

  confirmPayment: async (orderId, paymentIntentId) => {
    const res = await apiFetch(buildUrl('/payments/confirm/'), {
      method:  'POST',
      headers: getAuthHeaders(),
      body:    JSON.stringify({ order_id: orderId, payment_intent_id: paymentIntentId }),
    });
    return res.json();
  },

  getPaymentStatus: async (orderId) => {
    const res = await apiFetch(buildUrl(`/payments/order/${orderId}/`), {
      headers: getAuthHeaders(),
    });
    return res.json();
  },
};
