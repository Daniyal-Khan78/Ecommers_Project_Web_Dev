import React, { useEffect, useState } from 'react';
import { authAPI } from '../../../api/auth';
import Spinner from '../../../components/Spinner/Spinner';
import { AdminNav } from '../Dashboard/Dashboard';
import '../Admin.css';

const formatDate = (iso) =>
  new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

const ManageUsers = () => {
  const [users,   setUsers]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(null);

  useEffect(() => {
    authAPI.getUsers().then(d => {
      if (d.success) setUsers(d.data || []);
    }).finally(() => setLoading(false));
  }, []);

  const handleToggle = async (userId, field, newValue) => {
    setUpdating(userId + field);
    try {
      const data = await authAPI.updateUser(userId, { [field]: newValue });
      if (data.success) setUsers(prev => prev.map(u => u.id === userId ? data.data : u));
    } finally {
      setUpdating(null);
    }
  };

  return (
    <div className="admin-page">
      <div className="container">
        <h1>Manage Users</h1>
        <p className="admin-subtitle">View and manage customer accounts.</p>
        <AdminNav active="users" />

        <div className="admin-section">
          <div className="admin-section-header">
            <h2>All Users ({users.length})</h2>
          </div>

          {loading ? (
            <div style={{ padding: '2rem' }}><Spinner /></div>
          ) : (
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Email</th>
                    <th>Joined</th>
                    <th>Verified</th>
                    <th>Active</th>
                    <th>Admin</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td>
                        <div style={{ display:'flex', alignItems:'center', gap:'0.6rem' }}>
                          {u.profile_image_url ? (
                            <img src={u.profile_image_url} alt={u.username} style={{ width:32, height:32, borderRadius:'50%', objectFit:'cover' }} />
                          ) : (
                            <div style={{ width:32, height:32, borderRadius:'50%', background:'var(--light-gray)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'1rem' }}>👤</div>
                          )}
                          <div>
                            <div style={{ fontWeight:600, fontSize:'0.875rem' }}>{u.first_name || u.username}</div>
                            <div style={{ fontSize:'0.75rem', color:'var(--gray)' }}>@{u.username}</div>
                          </div>
                        </div>
                      </td>
                      <td style={{ fontSize:'0.875rem' }}>{u.email}</td>
                      <td style={{ fontSize:'0.875rem' }}>{formatDate(u.date_joined)}</td>
                      <td>
                        <span style={{
                          fontSize:'0.72rem', fontWeight:700, padding:'0.2rem 0.55rem', borderRadius:'50px',
                          background: u.email_verified ? '#d1fae5' : '#fef3c7',
                          color: u.email_verified ? '#065f46' : '#92400e',
                        }}>
                          {u.email_verified ? '✓ Yes' : '✗ No'}
                        </span>
                      </td>
                      <td>
                        <label className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={u.is_active}
                            onChange={() => handleToggle(u.id, 'is_active', !u.is_active)}
                            disabled={updating === u.id + 'is_active'}
                          />
                          <span className="toggle-slider" />
                        </label>
                      </td>
                      <td>
                        <label className="toggle-switch">
                          <input
                            type="checkbox"
                            checked={u.is_admin}
                            onChange={() => handleToggle(u.id, 'is_admin', !u.is_admin)}
                            disabled={updating === u.id + 'is_admin'}
                          />
                          <span className="toggle-slider" />
                        </label>
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

export default ManageUsers;
