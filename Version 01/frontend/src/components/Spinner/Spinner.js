import React from 'react';

// Centered loading spinner used while API data is being fetched.
// Uses the .spinner CSS class defined in App.css
const Spinner = ({ message = 'Loading...' }) => (
  <div style={{ textAlign: 'center', padding: '3rem' }}>
    <div className="spinner" aria-label="Loading" />
    {message && <p style={{ color: 'var(--gray)', marginTop: '1rem' }}>{message}</p>}
  </div>
);

export default Spinner;
