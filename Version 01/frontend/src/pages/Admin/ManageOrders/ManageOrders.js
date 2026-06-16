import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ordersAPI } from '../../../api/orders';
import Spinner from '../../../components/Spinner/Spinner';
import { AdminNav } from '../Dashboard/Dashboard';
import '../Admin.css';

const STATUS_OPTIONS = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled'];

const formatDate = (iso) =>
  new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

const ManageOrders = () => {
  const [orders,  setOrders]  = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter,  setFilter]  = useState('');
  const [updating, setUpdating] = useState(null); // order id being updated

  const loadOrders = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ordersAPI.getAllOrders(filter ? { status: filter } : {});
      if (data.success) setOrders(data.data || []);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { loadOrders(); }, [loadOrders]);

  const handleStatusChange = async (orderId, newStatus) => {
    setUpdating(orderId);
    try {
      const data = await ordersAPI.updateOrderStatus(orderId, newStatus);
      if (data.success) {
        setOrders(prev => prev.map(o => o.id === orderId ? data.data : o));
      }
    } finally {
      setUpdating(null);
    }
  };

  return (
    <div className="admin-page">
      <div className="container">
        <h1>Manage Orders</h1>
        <p className="admin-subtitle">View and update order statuses.</p>
        <AdminNav active="orders" />

        <div className="admin-section">
          <div className="admin-section-header">
            <h2>Orders {orders.length > 0 && `(${orders.length})`}</h2>
          </div>

          {/* Filter */}
          <div className="admin-filters">
            <select className="admin-filter-select" value={filter} onChange={e => setFilter(e.target.value)}>
              <option value="">All Statuses</option>
              {STATUS_OPTIONS.map(s => <option key={s} value={s} style={{ textTransform:'capitalize' }}>{s}</option>)}
            </select>
          </div>

          {loading ? (
            <div style={{ padding: '2rem' }}><Spinner /></div>
          ) : orders.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--gray)' }}>No orders found.</div>
          ) : (
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Order #</th>
                    <th>Date</th>
                    <th>Items</th>
                    <th>Total</th>
                    <th>Payment</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map(o => (
                    <tr key={o.id}>
                      <td><Link to={`/orders/${o.id}`}>#{o.id}</Link></td>
                      <td>{formatDate(o.created_at)}</td>
                      <td>{o.items?.length || 0}</td>
                      <td>${parseFloat(o.total_amount).toFixed(2)}</td>
                      <td style={{ fontSize:'0.8rem', textTransform:'capitalize' }}>
                        {o.payment?.payment_method === 'cod' ? 'COD' : 'Card'}
                        <br />
                        <span style={{ color: o.payment?.status === 'completed' ? 'var(--success)' : 'var(--gray)' }}>
                          {o.payment?.status || '—'}
                        </span>
                      </td>
                      <td>
                        <select
                          className="admin-filter-select"
                          value={o.status}
                          onChange={e => handleStatusChange(o.id, e.target.value)}
                          disabled={updating === o.id}
                          style={{ fontSize: '0.8rem', padding: '0.25rem 0.5rem' }}
                        >
                          {STATUS_OPTIONS.map(s => (
                            <option key={s} value={s} style={{ textTransform: 'capitalize' }}>{s}</option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <Link to={`/orders/${o.id}`} className="admin-action-btn" style={{ textDecoration:'none', display:'inline-block' }}>
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ManageOrders;
