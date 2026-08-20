import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../shared/context/AuthContext';
import api, { ApiError } from '../../shared/lib/api';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
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
      const data = await api.post<{ access?: string; access_token?: string; key?: string; user?: any }>('/auth/registration/', {
        email,
        password,
        password1: password,
        password2: confirmPassword,
        username: email
      });
      const token = data?.access || data?.access_token || data?.key;
      if (token && data?.user) {
        login(token, data.user);
        navigate('/');
      } else {
        navigate('/login');
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError('Registration failed. Email might be in use or password too weak.');
      } else {
        setError(String(err));
      }
    } finally {
      setIsSubmitting(false);
    }
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
        <h2 style={{ marginBottom: '24px', textAlign: 'center' }}>Create Account</h2>
        
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
            {isSubmitting ? 'Creating account...' : 'Sign Up'}
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

        <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '14px', color: 'var(--color-text-secondary)' }}>
          Already have an account? <Link to="/login" style={{ color: '#6366f1', textDecoration: 'none' }}>Log in</Link>
        </p>
      </div>
    </div>
  );
}
