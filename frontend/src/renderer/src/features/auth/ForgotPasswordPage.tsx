import { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../shared/lib/api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setIsSubmitting(true);
    
    try {
      await api.post('/auth/password/reset/', { email });
      setMessage('If an account exists, an email has been sent with reset instructions.');
    } catch (err) {
      setError('Failed to process request. Please try again later.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', background: 'var(--color-bg-primary)', color: 'var(--color-text-primary)' }}>
      <div style={{ width: '400px', padding: '40px', background: 'var(--color-bg-secondary)', borderRadius: '12px', boxShadow: '0 8px 30px rgba(0,0,0,0.5)' }}>
        <h2 style={{ marginBottom: '16px', textAlign: 'center' }}>Reset Password</h2>
        <p style={{ marginBottom: '24px', textAlign: 'center', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
          Enter your email address and we'll send you a link to reset your password.
        </p>
        
        {error && <div style={{ color: '#ff6b6b', background: 'rgba(255, 107, 107, 0.1)', padding: '10px', borderRadius: '6px', marginBottom: '20px' }}>{error}</div>}
        {message && <div style={{ color: '#2ecc71', background: 'rgba(46, 204, 113, 0.1)', padding: '10px', borderRadius: '6px', marginBottom: '20px' }}>{message}</div>}
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>Email</label>
            <input 
              type="email" 
              value={email} 
              onChange={e => setEmail(e.target.value)}
              required 
              style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-bg-primary)', color: 'var(--color-text-primary)' }}
            />
          </div>
          <button type="submit" disabled={isSubmitting} style={{ background: '#6366f1', color: '#fff', border: 'none', padding: '12px', borderRadius: '6px', cursor: isSubmitting ? 'not-allowed' : 'pointer', fontWeight: 600 }}>
            {isSubmitting ? 'Sending...' : 'Send Reset Link'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
          Remembered your password? <Link to="/login" style={{ color: '#6366f1', textDecoration: 'none' }}>Log in</Link>
        </p>
      </div>
    </div>
  );
}
