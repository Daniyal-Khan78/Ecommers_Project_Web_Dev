import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ordersAPI } from '../../api/orders';
import Spinner from '../../components/Spinner/Spinner';
import './Orders.css';

const formatDate = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
};

const payStatusClass = (s) => {
  if (!s) return '';
  const map = { completed: 'pay-completed', pending: 'pay-pending', failed: 'pay-failed', refunded: 'pay-refunded' };
  return map[s] || '';
};

const OrderDetail = () => {
  const { id } = useParams();

  const [order,     setOrder]     = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [cancelling, setCancelling] = useState(false);
  const [error,     setError]     = useState('');

  const loadOrder = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await ordersAPI.getOrder(id);
      if (data.success) {
        setOrder(data.data);
      } else {
        setError('Order not found.');
      }
    } catch {
      setError('Failed to load order.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { loadOrder(); }, [loadOrder]);

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel this order?')) return;
    setCancelling(true);
    try {
      const data = await ordersAPI.cancelOrder(id);
      if (data.success) {
        setOrder(data.data);
      } else {
        setError(data.message || 'Could not cancel order.');
      }
    } finally {
      setCancelling(false);
    }
  };

  if (loading) return <div className="container" style={{ padding: '4rem 0' }}><Spinner /></div>;
  if (error || !order) {
    return (
      <div className="container" style={{ padding: '4rem 0', textAlign: 'center' }}>
        <p style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{error || 'Order not found.'}</p>
        <Link to="/orders" className="btn btn-primary">Back to Orders</Link>
      </div>
    );
  }

  const canCancel = ['pending', 'confirmed'].includes(order.status);
  const payment   = order.payment;

  return (
    <div className="order-detail-page">
      <div className="container">

        {/* Header */}
        <div style={{ marginBottom: '0.25rem' }}>
          <Link to="/orders" style={{ fontSize: '0.875rem', color: 'var(--gray)' }}>← My Orders</Link>
        </div>
        <h1>Order #{order.id}</h1>
        <div className="order-detail-meta">
          <span className="order-detail-date">{formatDate(order.created_at)}</span>
          <span className={`order-status-badge status-${order.status}`}>
            {order.status_display || order.status}
          </span>
        </div>

        <div className="order-detail-grid">

          {/* Left column */}
          <div>
            {/* Items */}
            <div className="order-detail-section">
              <h2>Items Ordered</h2>
              <div className="order-items-list">
                {order.items?.map(item => (
                  <div className="order-item-row" key={item.id}>
                    {item.product?.primary_image_url ? (
                      <img
                        src={item.product.primary_image_url}
                        alt={item.product?.name}
                        className="order-item-img"
                        style={{ objectFit: 'cover' }}
                      />
                    ) : (
                      <div className="order-item-img">🛍️</div>
                    )}
                    <div className="order-item-info">
                      <div className="order-item-name">
                        {item.product ? (
                          <Link to={`/products/${item.product.id}`}>{item.product.name}</Link>
                        ) : 'Product removed'}
                      </div>
                      <div className="order-item-unit">
                        ${parseFloat(item.price).toFixed(2)} × {item.quantity}
                      </div>
                    </div>
                    <span className="order-item-subtotal">${parseFloat(item.subtotal).toFixed(2)}</span>
                  </div>
                ))}
              </div>

              <div className="order-detail-total">
                <span>Total</span>
                <span>${parseFloat(order.total_amount).toFixed(2)}</span>
              </div>
            </div>

            {/* Shipping */}
            <div className="order-detail-section">
              <h2>Shipping Address</h2>
              <p style={{ color: 'var(--gray)', lineHeight: 1.7, whiteSpace: 'pre-line' }}>
                {order.shipping_address}
              </p>
              {order.notes && (
                <p style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--gray)' }}>
                  <strong>Notes:</strong> {order.notes}
                </p>
              )}
            </div>
          </div>

          {/* Right column */}
          <div>
            {/* Payment info */}
            <div className="order-detail-section">
              <h2>Payment</h2>
              {payment ? (
                <>
                  <div className="info-row">
                    <span className="info-row-label">Method</span>
                    <span className="info-row-value" style={{ textTransform: 'capitalize' }}>
                      {payment.payment_method === 'cod' ? 'Cash on Delivery' : 'Credit / Debit Card'}
                    </span>
                  </div>
                  <div className="info-row">
                    <span className="info-row-label">Status</span>
                    <span className={`payment-status-badge ${payStatusClass(payment.status)}`}>
                      {payment.status}
                    </span>
                  </div>
                  <div className="info-row">
                    <span className="info-row-label">Amount</span>
                    <span className="info-row-value">${parseFloat(payment.amount).toFixed(2)}</span>
                  </div>
                  {payment.paid_at && (
                    <div className="info-row">
                      <span className="info-row-label">Paid at</span>
                      <span className="info-row-value" style={{ fontSize: '0.8rem' }}>{formatDate(payment.paid_at)}</span>
                    </div>
                  )}
                </>
              ) : (
                <p style={{ color: 'var(--gray)', fontSize: '0.9rem' }}>No payment record.</p>
              )}
            </div>

            {/* Cancel button */}
            {canCancel && (
              <div className="order-detail-section" style={{ padding: '1rem 1.5rem' }}>
                <button
                  className="btn-cancel-order"
                  onClick={handleCancel}
                  disabled={cancelling}
                >
                  {cancelling ? 'Cancelling...' : 'Cancel Order'}
                </button>
              </div>
            )}

            {error && (
              <div style={{ color: 'var(--danger)', fontSize: '0.9rem', marginTop: '0.5rem' }}>{error}</div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};

export default OrderDetail;
