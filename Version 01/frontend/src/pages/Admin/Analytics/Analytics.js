import React, { useEffect, useState } from 'react';
import { ordersAPI } from '../../../api/orders';
import Spinner from '../../../components/Spinner/Spinner';
import { AdminNav } from '../Dashboard/Dashboard';
import '../Admin.css';

const STATUS_COLORS = {
  pending:   '#f59e0b',
  confirmed: '#3b82f6',
  shipped:   '#8b5cf6',
  delivered: '#10b981',
  cancelled: '#ef4444',
};

const Analytics = () => {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ordersAPI.getAnalytics().then(d => {
      if (d.success) setData(d.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="container" style={{ padding: '4rem 0' }}><Spinner /></div>;

  const daily = data?.daily_orders || [];
  const statusCounts = data?.status_counts || {};
  const maxRevenue = Math.max(...daily.map(d => parseFloat(d.revenue || 0)), 1);
  const totalStatusOrders = Object.values(statusCounts).reduce((a, b) => a + b, 0) || 1;

  return (
    <div className="admin-page">
      <div className="container">
        <h1>Analytics</h1>
        <p className="admin-subtitle">Store performance over the last 30 days.</p>
        <AdminNav active="analytics" />

        {/* Summary stats */}
        <div className="stats-grid" style={{ marginBottom: '2rem' }}>
          <div className="stat-card">
            <div className="stat-icon blue">📦</div>
            <div className="stat-info">
              <div className="stat-value">{data?.total_orders ?? 0}</div>
              <div className="stat-label">Total Orders</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon green">💰</div>
            <div className="stat-info">
              <div className="stat-value">${parseFloat(data?.total_revenue || 0).toFixed(0)}</div>
              <div className="stat-label">Total Revenue</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon amber">✅</div>
            <div className="stat-info">
              <div className="stat-value">{statusCounts.delivered || 0}</div>
              <div className="stat-label">Delivered</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon purple">⏳</div>
            <div className="stat-info">
              <div className="stat-value">{statusCounts.pending || 0}</div>
              <div className="stat-label">Pending</div>
            </div>
          </div>
        </div>

        {/* Revenue chart */}
        <div className="chart-section">
          <h2>Daily Revenue — Last 30 Days</h2>
          {daily.length === 0 ? (
            <p style={{ color: 'var(--gray)', fontSize: '0.9rem' }}>No order data for the last 30 days.</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <div className="bar-chart" style={{ minWidth: `${daily.length * 28}px` }}>
                {daily.map((d, i) => {
                  const rev = parseFloat(d.revenue || 0);
                  const heightPct = (rev / maxRevenue) * 100;
                  const shortDate = d.date.slice(5); // MM-DD
                  return (
                    <div key={i} className="bar-chart-bar-wrap" title={`${d.date}: $${rev.toFixed(2)} (${d.orders} orders)`}>
                      <div
                        className="bar-chart-bar"
                        style={{ height: `${Math.max(heightPct, 1)}%` }}
                      />
                      <span className="bar-chart-label">{shortDate}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Orders by status */}
        <div className="chart-section">
          <h2>Orders by Status</h2>
          <div className="status-bars">
            {Object.entries(statusCounts).map(([status, count]) => (
              <div className="status-bar-row" key={status}>
                <span className="status-bar-label">{status}</span>
                <div className="status-bar-track">
                  <div
                    className="status-bar-fill"
                    style={{
                      width: `${(count / totalStatusOrders) * 100}%`,
                      background: STATUS_COLORS[status] || 'var(--primary)',
                    }}
                  />
                </div>
                <span className="status-bar-count">{count}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default Analytics;
