import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../shared/context/AuthContext';
import api, { ApiError } from '../../shared/lib/api';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    
    try {
      const data = await api.post<{ access?: string; access_token?: string; key?: string; user: any }>('/auth/login/', {
        email,
        password
      });
      
      const token = data.access || data.access_token || data.key || '';
      login(token, data.user);
      navigate('/');
    } catch (err) {
      if (err instanceof ApiError) {
        setError('Invalid credentials or server error.');
      } else {
        setError(String(err));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOAuth = (provider: string) => {
    window.location.href = `http://127.0.0.1:8000/api/auth/${provider}/login/`;
  };

  const handleGuestLogin = async () => {
    setError('');
    setIsSubmitting(true);
    try {
      const data = await api.post<{ access: string; user: any }>('/auth/guest/');
      login(data.access, data.user);
      navigate('/');
    } catch (err) {
      setError('Guest login failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', justifyContent: 'center', alignItems: 'center', background: 'var(--color-bg-primary)', color: 'var(--color-text-primary)' }}>
      <div style={{ width: '400px', padding: '40px', background: 'var(--color-bg-secondary)', borderRadius: '12px', boxShadow: '0 8px 30px rgba(0,0,0,0.5)' }}>
        <h2 style={{ marginBottom: '24px', textAlign: 'center' }}>Welcome Back</h2>
        
        {error && <div style={{ color: '#ff6b6b', background: 'rgba(255, 107, 107, 0.1)', padding: '10px', borderRadius: '6px', marginBottom: '20px' }}>{error}</div>}
        
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
          <div>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={e => setPassword(e.target.value)}
              required 
              style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-bg-primary)', color: 'var(--color-text-primary)' }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Link to="/forgot-password" style={{ fontSize: '12px', color: '#6366f1', textDecoration: 'none' }}>Forgot Password?</Link>
          </div>
          <button type="submit" disabled={isSubmitting} style={{ background: '#6366f1', color: '#fff', border: 'none', padding: '12px', borderRadius: '6px', cursor: isSubmitting ? 'not-allowed' : 'pointer', fontWeight: 600 }}>
            {isSubmitting ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        <button 
          type="button"
          onClick={handleGuestLogin}
          disabled={isSubmitting}
          style={{ 
            width: '100%', 
            marginTop: '12px',
            background: 'var(--color-bg-tertiary, #1f293d)', 
            color: 'var(--color-text-primary)', 
            border: '1px dashed var(--color-border)', 
            padding: '11px', 
            borderRadius: '6px', 
            cursor: isSubmitting ? 'not-allowed' : 'pointer', 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            gap: '8px',
            fontWeight: 500,
            fontSize: '14px',
            transition: 'all 0.2s'
          }}
          onMouseEnter={e => e.currentTarget.style.borderColor = '#6366f1'}
          onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--color-border)'}
        >
          👤 Continue as Guest
        </button>

        <div style={{ display: 'flex', alignItems: 'center', margin: '20px 0' }}>
          <div style={{ flex: 1, height: '1px', background: 'var(--color-border)' }}></div>
          <span style={{ padding: '0 10px', fontSize: '12px', color: 'var(--color-text-secondary)' }}>OR</span>
          <div style={{ flex: 1, height: '1px', background: 'var(--color-border)' }}></div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => handleOAuth('google')} style={{ flex: 1, background: 'var(--color-bg-primary)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border)', padding: '10px', borderRadius: '6px', cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
            Google
          </button>
          <button onClick={() => handleOAuth('github')} style={{ flex: 1, background: 'var(--color-bg-primary)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border)', padding: '10px', borderRadius: '6px', cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
            GitHub
          </button>
        </div>

        <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
          Don't have an account? <Link to="/register" style={{ color: '#6366f1', textDecoration: 'none' }}>Sign up</Link>
        </p>
      </div>
    </div>
  );
}
