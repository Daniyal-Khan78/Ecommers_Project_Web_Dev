import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ordersAPI } from '../../../api/orders';
import { productsAPI } from '../../../api/products';
import { authAPI } from '../../../api/auth';
import Spinner from '../../../components/Spinner/Spinner';
import '../Admin.css';

const AdminNav = ({ active }) => (
  <nav className="admin-nav">
    <Link to="/admin"             className={active === 'dashboard' ? 'active' : ''}>Dashboard</Link>
    <Link to="/admin/products"    className={active === 'products'  ? 'active' : ''}>Products</Link>
    <Link to="/admin/orders"      className={active === 'orders'    ? 'active' : ''}>Orders</Link>
    <Link to="/admin/users"       className={active === 'users'     ? 'active' : ''}>Users</Link>
    <Link to="/admin/analytics"   className={active === 'analytics' ? 'active' : ''}>Analytics</Link>
  </nav>
);

export { AdminNav };

const formatDate = (iso) =>
  new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

const Dashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [userCount, setUserCount] = useState('—');
  const [productCount, setProductCount] = useState('—');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      ordersAPI.getAnalytics(),
      authAPI.getUsers(),
      productsAPI.getAllProductsAdmin(),
    ]).then(([a, u, p]) => {
      if (a.success) setAnalytics(a.data);
      if (u.success) setUserCount((u.data || []).length);
      if (p.success) setProductCount(p.count || (p.data || []).length);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="container" style={{ padding: '4rem 0' }}><Spinner /></div>;

  return (
    <div className="admin-page">
      <div className="container">
        <h1>Admin Dashboard</h1>
        <p className="admin-subtitle">Overview of your store.</p>
        <AdminNav active="dashboard" />

        {/* Stats */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon blue">📦</div>
            <div className="stat-info">
              <div className="stat-value">{analytics?.total_orders ?? '—'}</div>
              <div className="stat-label">Total Orders</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon green">💰</div>
            <div className="stat-info">
              <div className="stat-value">${analytics ? parseFloat(analytics.total_revenue).toFixed(0) : '—'}</div>
              <div className="stat-label">Revenue</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon amber">🛍️</div>
            <div className="stat-info">
              <div className="stat-value">{productCount}</div>
              <div className="stat-label">Products</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon purple">👥</div>
            <div className="stat-info">
              <div className="stat-value">{userCount}</div>
              <div className="stat-label">Users</div>
            </div>
          </div>
        </div>

        {/* Quick links */}
        <div className="quick-links">
          <Link to="/admin/products" className="quick-link-card">
            <span className="quick-link-icon">🛍️</span>
            <span className="quick-link-label">Manage Products</span>
          </Link>
          <Link to="/admin/orders" className="quick-link-card">
            <span className="quick-link-icon">📦</span>
            <span className="quick-link-label">Manage Orders</span>
          </Link>
          <Link to="/admin/users" className="quick-link-card">
            <span className="quick-link-icon">👥</span>
            <span className="quick-link-label">Manage Users</span>
          </Link>
          <Link to="/admin/analytics" className="quick-link-card">
            <span className="quick-link-icon">📊</span>
            <span className="quick-link-label">Analytics</span>
          </Link>
        </div>

        {/* Recent orders */}
        {analytics?.recent_orders?.length > 0 && (
          <div className="admin-section">
            <div className="admin-section-header">
              <h2>Recent Orders</h2>
              <Link to="/admin/orders" style={{ fontSize: '0.85rem' }}>View all →</Link>
            </div>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Order #</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Items</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.recent_orders.map(o => (
                    <tr key={o.id}>
                      <td><Link to={`/orders/${o.id}`}>#{o.id}</Link></td>
                      <td>{formatDate(o.created_at)}</td>
                      <td>
                        <span className={`order-status-badge status-${o.status}`} style={{ fontSize:'0.72rem', padding:'0.2rem 0.55rem', borderRadius:'50px', fontWeight:700 }}>
                          {o.status_display || o.status}
                        </span>
                      </td>
                      <td>{o.items?.length || 0}</td>
                      <td>${parseFloat(o.total_amount).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
