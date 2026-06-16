import React, { useEffect, useState, useRef } from 'react';
import { authAPI } from '../../api/auth';
import { useAuth } from '../../context/AuthContext';
import Spinner from '../../components/Spinner/Spinner';
import './Profile.css';

const Profile = () => {
  const { updateUser } = useAuth();

  const [profile,   setProfile]   = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [saving,    setSaving]    = useState(false);
  const [pwSaving,  setPwSaving]  = useState(false);
  const [profileMsg, setProfileMsg] = useState({ type: '', text: '' });
  const [pwMsg,     setPwMsg]     = useState({ type: '', text: '' });
  const [resending, setResending] = useState(false);
  const [resendMsg, setResendMsg] = useState('');

  const fileInputRef = useRef(null);

  // Edit form state
  const [form, setForm] = useState({
    first_name: '', last_name: '', phone: '', address: '',
  });

  // Password form state
  const [pwForm, setPwForm] = useState({
    old_password: '', new_password: '', confirm_password: '',
  });

  useEffect(() => {
    authAPI.getProfile().then(data => {
      if (data.success) {
        setProfile(data.data);
        setForm({
          first_name: data.data.first_name || '',
          last_name:  data.data.last_name  || '',
          phone:      data.data.phone      || '',
          address:    data.data.address    || '',
        });
      }
    }).finally(() => setLoading(false));
  }, []);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setProfileMsg({ type: '', text: '' });

    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => fd.append(k, v));

    const data = await authAPI.updateProfile(fd);
    if (data.success) {
      setProfile(data.data);
      updateUser(data.data);
      setProfileMsg({ type: 'success', text: 'Profile updated successfully.' });
    } else {
      const errText = data.message || Object.values(data.errors || {})[0]?.[0] || 'Update failed.';
      setProfileMsg({ type: 'error', text: errText });
    }
    setSaving(false);
  };

  const handleAvatarChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('profile_image', file);
    const data = await authAPI.updateProfile(fd);
    if (data.success) {
      setProfile(data.data);
      updateUser(data.data);
    }
  };

  const handlePasswordSave = async (e) => {
    e.preventDefault();
    setPwMsg({ type: '', text: '' });
    if (pwForm.new_password !== pwForm.confirm_password) {
      setPwMsg({ type: 'error', text: 'New passwords do not match.' });
      return;
    }
    setPwSaving(true);
    const data = await authAPI.changePassword(pwForm);
    if (data.success) {
      setPwMsg({ type: 'success', text: 'Password changed successfully.' });
      setPwForm({ old_password: '', new_password: '', confirm_password: '' });
    } else {
      const errText = data.message || Object.values(data.errors || {})[0]?.[0] || 'Password change failed.';
      setPwMsg({ type: 'error', text: errText });
    }
    setPwSaving(false);
  };

  const handleResendVerification = async () => {
    setResending(true);
    setResendMsg('');
    const data = await authAPI.resendVerification();
    setResendMsg(data.message || (data.success ? 'Sent!' : 'Failed to send.'));
    setResending(false);
  };

  if (loading) return <div className="container" style={{ padding: '4rem 0' }}><Spinner /></div>;
  if (!profile) return null;

  const displayName = [profile.first_name, profile.last_name].filter(Boolean).join(' ') || profile.username;

  return (
    <div className="profile-page">
      <div className="container">
        <h1>My Profile</h1>

        <div className="profile-layout">

          {/* Avatar panel */}
          <div className="profile-avatar-panel">
            <div className="avatar-img-wrap">
              {profile.profile_image_url ? (
                <img src={profile.profile_image_url} alt={displayName} className="avatar-img" />
              ) : (
                <div className="avatar-placeholder">👤</div>
              )}
              <label className="avatar-upload-label" htmlFor="avatar-input" title="Change photo">
                ✏️
              </label>
              <input
                id="avatar-input"
                ref={fileInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={handleAvatarChange}
              />
            </div>
            <div className="avatar-name">{displayName}</div>
            <div className="avatar-email">{profile.email}</div>
            {profile.is_admin && (
              <span className="avatar-badge">⭐ Admin</span>
            )}
          </div>

          {/* Right panel */}
          <div>

            {/* Edit info */}
            <div className="profile-section">
              <h2>Personal Information</h2>
              <form onSubmit={handleProfileSave}>
                <div className="profile-form-row">
                  <div className="form-group">
                    <label className="form-label">First Name</label>
                    <input
                      type="text"
                      className="form-control"
                      value={form.first_name}
                      onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Last Name</label>
                    <input
                      type="text"
                      className="form-control"
                      value={form.last_name}
                      onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Phone</label>
                  <input
                    type="tel"
                    className="form-control"
                    placeholder="+1 555 123 4567"
                    value={form.phone}
                    onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Default Address</label>
                  <textarea
                    className="form-control"
                    rows={3}
                    placeholder="Street, City, State, ZIP"
                    value={form.address}
                    onChange={e => setForm(f => ({ ...f, address: e.target.value }))}
                  />
                </div>
                {profileMsg.text && (
                  <div className={`profile-alert ${profileMsg.type}`}>{profileMsg.text}</div>
                )}
                <button type="submit" className="btn btn-primary" disabled={saving} style={{ marginTop: '1rem' }}>
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </form>
            </div>

            {/* Email verification */}
            <div className="profile-section">
              <h2>Email Verification</h2>
              <div className="verify-status">
                <div>
                  <strong>{profile.email}</strong>
                  <div style={{ fontSize: '0.85rem', color: 'var(--gray)', marginTop: '0.25rem' }}>
                    {profile.email_verified
                      ? 'Your email address is verified.'
                      : 'Please verify your email to complete your account.'}
                  </div>
                </div>
                <span className={`verify-badge ${profile.email_verified ? 'verified' : 'unverified'}`}>
                  {profile.email_verified ? '✓ Verified' : '⚠ Unverified'}
                </span>
              </div>
              {!profile.email_verified && (
                <div style={{ marginTop: '0.75rem' }}>
                  <button
                    className="btn btn-primary"
                    onClick={handleResendVerification}
                    disabled={resending}
                    style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                  >
                    {resending ? 'Sending...' : 'Resend Verification Email'}
                  </button>
                  {resendMsg && (
                    <span style={{ marginLeft: '0.75rem', fontSize: '0.85rem', color: 'var(--success)' }}>
                      {resendMsg}
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Change password */}
            <div className="profile-section">
              <h2>Change Password</h2>
              <form onSubmit={handlePasswordSave}>
                <div className="form-group">
                  <label className="form-label">Current Password</label>
                  <input
                    type="password"
                    className="form-control"
                    value={pwForm.old_password}
                    onChange={e => setPwForm(f => ({ ...f, old_password: e.target.value }))}
                    required
                  />
                </div>
                <div className="profile-form-row">
                  <div className="form-group">
                    <label className="form-label">New Password</label>
                    <input
                      type="password"
                      className="form-control"
                      value={pwForm.new_password}
                      onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))}
                      required
                      minLength={8}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Confirm New Password</label>
                    <input
                      type="password"
                      className="form-control"
                      value={pwForm.confirm_password}
                      onChange={e => setPwForm(f => ({ ...f, confirm_password: e.target.value }))}
                      required
                    />
                  </div>
                </div>
                {pwMsg.text && (
                  <div className={`profile-alert ${pwMsg.type}`}>{pwMsg.text}</div>
                )}
                <button type="submit" className="btn btn-primary" disabled={pwSaving} style={{ marginTop: '1rem' }}>
                  {pwSaving ? 'Changing...' : 'Change Password'}
                </button>
              </form>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
