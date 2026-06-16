import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authAPI } from '../../api/auth';
import { useAuth } from '../../context/AuthContext';
import './Login.css';

const Login = () => {
  const { login } = useAuth();
  const navigate  = useNavigate();
  const location  = useLocation();

  // Redirect back to the page the user was trying to visit before login
  const from = location.state?.from?.pathname || '/';

  const [formData, setFormData] = useState({ email: '', password: '' });
  const [errors,   setErrors]   = useState({});
  const [apiError, setApiError] = useState('');
  const [loading,  setLoading]  = useState(false);

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    if (errors[e.target.name]) setErrors(prev => ({ ...prev, [e.target.name]: '' }));
    setApiError('');
  };

  // Client-side validation before hitting the API
  const validate = () => {
    const errs = {};
    if (!formData.email)    errs.email    = 'Email is required.';
    else if (!/\S+@\S+\.\S+/.test(formData.email)) errs.email = 'Enter a valid email address.';
    if (!formData.password) errs.password = 'Password is required.';
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setLoading(true);
    try {
      const data = await authAPI.login(formData.email, formData.password);

      if (data.success) {
        login(data.data.user, data.data.tokens);
        navigate(from, { replace: true });
      } else {
        setApiError(data.message || 'Login failed. Please try again.');
        if (data.errors) {
          const fieldErrors = {};
          Object.keys(data.errors).forEach(k => {
            fieldErrors[k] = Array.isArray(data.errors[k]) ? data.errors[k][0] : data.errors[k];
          });
          setErrors(fieldErrors);
        }
      }
    } catch {
      setApiError('Network error. Please check your connection and try again.');
    }
    setLoading(false);
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <Link to="/" className="auth-logo">🛍️ ShopNest</Link>
          <h1>Welcome Back</h1>
          <p>Sign in to your account to continue shopping</p>
        </div>

        {apiError && <div className="alert alert-error">{apiError}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email" name="email" type="email"
              value={formData.email} onChange={handleChange}
              className={errors.email ? 'input-error' : ''}
              placeholder="you@example.com"
              autoComplete="email"
            />
            {errors.email && <span className="error-msg">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password" name="password" type="password"
              value={formData.password} onChange={handleChange}
              className={errors.password ? 'input-error' : ''}
              placeholder="Enter your password"
              autoComplete="current-password"
            />
            {errors.password && <span className="error-msg">{errors.password}</span>}
          </div>

          <button type="submit" className="btn btn-primary auth-submit-btn" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="auth-switch">
          Don't have an account? <Link to="/register">Create one free</Link>
        </p>

        {/* Quick fill for testing */}
        <div className="test-credentials">
          <p>Test accounts:</p>
          <button onClick={() => setFormData({ email: 'john@shopnest.com', password: 'SecurePass@123' })}>
            Customer Login
          </button>
          <button onClick={() => setFormData({ email: 'admin@shopnest.com', password: 'Admin@123456' })}>
            Admin Login
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
