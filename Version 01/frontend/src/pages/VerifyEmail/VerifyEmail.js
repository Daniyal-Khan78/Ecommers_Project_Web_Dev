import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { authAPI } from '../../api/auth';
import Spinner from '../../components/Spinner/Spinner';

const VerifyEmail = () => {
  const { token } = useParams();
  const [status,  setStatus]  = useState('loading'); // 'loading' | 'success' | 'error'
  const [message, setMessage] = useState('');

  useEffect(() => {
    authAPI.verifyEmail(token).then(data => {
      if (data.success) {
        setStatus('success');
        setMessage(data.message);
      } else {
        setStatus('error');
        setMessage(data.message || 'Verification failed.');
      }
    }).catch(() => {
      setStatus('error');
      setMessage('Network error. Please try again.');
    });
  }, [token]);

  return (
    <div style={{
      minHeight: '60vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', padding: '2rem',
    }}>
      <div style={{
        background: 'var(--white)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', padding: '2.5rem',
        maxWidth: '460px', width: '100%', textAlign: 'center',
        boxShadow: 'var(--shadow-md)',
      }}>
        {status === 'loading' && (
          <>
            <Spinner />
            <p style={{ color: 'var(--gray)', marginTop: '1rem' }}>Verifying your email…</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>✅</div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              Email Verified!
            </h1>
            <p style={{ color: 'var(--gray)', marginBottom: '1.5rem' }}>{message}</p>
            <Link to="/" className="btn btn-primary">Go to Home</Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>❌</div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              Verification Failed
            </h1>
            <p style={{ color: 'var(--danger)', marginBottom: '1.5rem' }}>{message}</p>
            <Link to="/profile" className="btn btn-primary">
              Resend Verification Email
            </Link>
          </>
        )}
      </div>
    </div>
  );
};

export default VerifyEmail;
