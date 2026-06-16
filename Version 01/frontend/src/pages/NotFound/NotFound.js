import React from 'react';
import { Link } from 'react-router-dom';

const NotFound = () => (
  <div style={{ textAlign: 'center', padding: '6rem 1rem' }}>
    <div style={{ fontSize: '5rem', marginBottom: '1rem' }}>🔍</div>
    <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>404 — Page Not Found</h1>
    <p style={{ color: 'var(--gray)', marginBottom: '2rem' }}>
      The page you're looking for doesn't exist or has been moved.
    </p>
    <Link to="/" className="btn btn-primary" style={{ marginRight: '1rem' }}>Go Home</Link>
    <Link to="/products" className="btn btn-secondary">Browse Products</Link>
  </div>
);

export default NotFound;
