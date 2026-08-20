import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../../shared/lib/api';

export default function ResetPasswordPage() {
  const { uid, token } = useParams<{ uid: string, token: string }>();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (password !== confirmPassword) {
      setError("Passwords don't match");
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post('/auth/password/reset/confirm/', {
        uid,
        token,
        new_password: password,
      });
      setMessage('Password successfully reset. Redirecting to login...');
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setError('Invalid or expired reset link. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', background: 'var(--color-bg-primary)', color: 'var(--color-text-primary)' }}>
      <div style={{ width: '400px', padding: '40px', background: 'var(--color-bg-secondary)', borderRadius: '12px', boxShadow: '0 8px 30px rgba(0,0,0,0.5)' }}>
        <h2 style={{ marginBottom: '24px', textAlign: 'center' }}>Set New Password</h2>
        
        {error && <div style={{ color: '#ff6b6b', background: 'rgba(255, 107, 107, 0.1)', padding: '10px', borderRadius: '6px', marginBottom: '20px' }}>{error}</div>}
        {message && <div style={{ color: '#2ecc71', background: 'rgba(46, 204, 113, 0.1)', padding: '10px', borderRadius: '6px', marginBottom: '20px' }}>{message}</div>}
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>New Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={e => setPassword(e.target.value)}
              required 
              style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-bg-primary)', color: 'var(--color-text-primary)' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>Confirm Password</label>
            <input 
              type="password" 
              value={confirmPassword} 
              onChange={e => setConfirmPassword(e.target.value)}
              required 
              style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-bg-primary)', color: 'var(--color-text-primary)' }}
            />
          </div>
          <button type="submit" disabled={isSubmitting} style={{ background: '#6366f1', color: '#fff', border: 'none', padding: '12px', borderRadius: '6px', cursor: isSubmitting ? 'not-allowed' : 'pointer', fontWeight: 600, marginTop: '8px' }}>
            {isSubmitting ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
          <Link to="/login" style={{ color: '#6366f1', textDecoration: 'none' }}>Back to Login</Link>
        </p>
      </div>
    </div>
  );
}
