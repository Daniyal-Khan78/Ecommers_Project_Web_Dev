import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../../api/auth';
import { useAuth } from '../../context/AuthContext';
import './Register.css';

const Field = ({ name, label, type = 'text', placeholder, required = true, formData, errors, handleChange }) => (
  <div className="form-group">
    <label htmlFor={name}>{label}{required && ' *'}</label>
    <input
      id={name} name={name} type={type}
      value={formData[name]} onChange={handleChange}
      className={errors[name] ? 'input-error' : ''}
      placeholder={placeholder}
      autoComplete={name}
    />
    {errors[name] && <span className="error-msg">{errors[name]}</span>}
  </div>
);

const Register = () => {
  const { login } = useAuth();
  const navigate  = useNavigate();

  const [formData, setFormData] = useState({
    first_name: '', last_name: '', username: '',
    email: '', password: '', password2: '', phone: '',
  });
  const [errors,   setErrors]   = useState({});
  const [apiError, setApiError] = useState('');
  const [loading,  setLoading]  = useState(false);

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
    if (errors[e.target.name]) setErrors(prev => ({ ...prev, [e.target.name]: '' }));
    setApiError('');
  };

  const validate = () => {
    const errs = {};
    if (!formData.first_name.trim()) errs.first_name = 'First name is required.';
    if (!formData.last_name.trim())  errs.last_name  = 'Last name is required.';
    if (!formData.username.trim())   errs.username   = 'Username is required.';
    else if (/\s/.test(formData.username)) errs.username = 'Username cannot contain spaces.';
    if (!formData.email.trim())      errs.email      = 'Email is required.';
    else if (!/\S+@\S+\.\S+/.test(formData.email)) errs.email = 'Enter a valid email.';
    if (!formData.password)          errs.password   = 'Password is required.';
    else if (formData.password.length < 8) errs.password = 'Password must be at least 8 characters.';
    if (formData.password !== formData.password2) errs.password2 = 'Passwords do not match.';
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setLoading(true);
    try {
      const data = await authAPI.register(formData);

      if (data.success) {
        login(data.data.user, data.data.tokens);
        navigate('/');
      } else {
        setApiError(data.message || 'Registration failed.');
        if (data.errors) {
          const fieldErrors = {};
          Object.keys(data.errors).forEach(k => {
            fieldErrors[k] = Array.isArray(data.errors[k]) ? data.errors[k][0] : data.errors[k];
          });
          setErrors(fieldErrors);
        }
      }
    } catch {
      setApiError('Network error. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="auth-page">
      <div className="auth-card register-card">
        <div className="auth-header">
          <Link to="/" className="auth-logo">🛍️ ShopNest</Link>
          <h1>Create Your Account</h1>
          <p>Join thousands of happy shoppers</p>
        </div>

        {apiError && <div className="alert alert-error">{apiError}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-row">
            <Field name="first_name" label="First Name" placeholder="John"        formData={formData} errors={errors} handleChange={handleChange} />
            <Field name="last_name"  label="Last Name"  placeholder="Doe"         formData={formData} errors={errors} handleChange={handleChange} />
          </div>

          <Field name="username"  label="Username"         placeholder="johndoe"            formData={formData} errors={errors} handleChange={handleChange} />
          <Field name="email"     label="Email"     type="email"    placeholder="john@example.com"   formData={formData} errors={errors} handleChange={handleChange} />
          <Field name="phone"     label="Phone"     type="tel"      placeholder="+92 300 1234567" required={false} formData={formData} errors={errors} handleChange={handleChange} />
          <Field name="password"  label="Password"  type="password" placeholder="Min. 8 characters"  formData={formData} errors={errors} handleChange={handleChange} />
          <Field name="password2" label="Confirm Password" type="password" placeholder="Repeat password" formData={formData} errors={errors} handleChange={handleChange} />

          <button type="submit" className="btn btn-primary auth-submit-btn" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account — It\'s Free!'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
