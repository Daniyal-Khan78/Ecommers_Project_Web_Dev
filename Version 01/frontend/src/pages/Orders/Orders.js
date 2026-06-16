import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ordersAPI } from '../../api/orders';
import Spinner from '../../components/Spinner/Spinner';
import './Orders.css';

const STATUS_TABS = [
  { value: '', label: 'All' },
  { value: 'pending',   label: 'Pending' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'shipped',   label: 'Shipped' },
  { value: 'delivered', label: 'Delivered' },
  { value: 'cancelled', label: 'Cancelled' },
];

const formatDate = (iso) =>
  new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });

const Orders = () => {
  const [orders,  setOrders]  = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab,     setTab]     = useState('');

  const loadOrders = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ordersAPI.getOrders(tab ? { status: tab } : {});
      if (data.success) setOrders(data.data || []);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => { loadOrders(); }, [loadOrders]);

  return (
    <div className="orders-page">
      <div className="container">
        <h1>My Orders</h1>

        {/* Status filter tabs */}
        <div className="orders-tabs">
          {STATUS_TABS.map(t => (
            <button
              key={t.value}
              className={`orders-tab ${tab === t.value ? 'active' : ''}`}
              onClick={() => setTab(t.value)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {loading ? (
          <Spinner />
        ) : orders.length === 0 ? (
          <div className="orders-empty">
            <div className="orders-empty-icon">📦</div>
            <h2>No orders yet</h2>
            <p>Start shopping to see your orders here.</p>
            <Link to="/products" className="btn btn-primary">Shop Now</Link>
          </div>
        ) : (
          <div className="orders-list">
            {orders.map(order => (
              <Link to={`/orders/${order.id}`} className="order-card" key={order.id}>
                <div className="order-card-header">
                  <div>
                    <div className="order-id">Order #{order.id}</div>
                    <div className="order-date">{formatDate(order.created_at)}</div>
                  </div>
                  <span className={`order-status-badge status-${order.status}`}>
                    {order.status_display || order.status}
                  </span>
                </div>
                <div className="order-card-body">
                  <span className="order-items-preview">
                    {order.items?.length || 0} item{(order.items?.length || 0) !== 1 ? 's' : ''}
                  </span>
                  <span className="order-total">${parseFloat(order.total_amount).toFixed(2)}</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Orders;
