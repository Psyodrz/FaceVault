import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock, ShieldAlert, ArrowRight, Loader2 } from 'lucide-react';
import logo from '../assets/logo.png';

const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const result = await login(username, password);
    if (!result.success) {
      setError(result.message || 'Invalid credentials');
    } else {
      navigate('/');
    }
    setLoading(false);
  };

  return (
    <div className="auth-container">
      <div className="auth-card fade-in">
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
            <div style={{ width: '100px', height: '100px' }}>
              <img src={logo} alt="FaceVault" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
            </div>
          </div>
          <h1 style={{ fontSize: '1.8rem', color: 'var(--text-primary)', marginBottom: '8px' }}>FaceVault Sentinel</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', fontWeight: '500' }}>Authorized Personnel Only</p>
        </div>

        {error && (
          <div className="badge badge-red" style={{ 
            width: '100%', 
            padding: '12px', 
            borderRadius: 'var(--radius-sm)', 
            marginBottom: '24px', 
            justifyContent: 'flex-start',
            textTransform: 'none',
            fontSize: '0.85rem'
          }}>
            <ShieldAlert size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="input-group">
            <label className="input-label">Operator ID</label>
            <input 
              type="text" 
              className="input" 
              value={username} 
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter username"
              required 
            />
          </div>
          
          <div className="input-group">
            <label className="input-label">Security Passcode</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ 
                position: 'absolute', 
                left: '14px', 
                top: '50%', 
                transform: 'translateY(-50%)', 
                color: 'var(--text-muted)',
                opacity: 0.7
              }} />
              <input 
                type="password" 
                className="input" 
                style={{ paddingLeft: '44px' }}
                value={password} 
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                required 
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary" style={{ marginTop: '12px' }} disabled={loading}>
            {loading ? (
              <><Loader2 size={18} className="animate-spin" /> Verifying...</>
            ) : (
              <><ArrowRight size={18} /> Secure Login</>
            )}
          </button>
        </form>

        <div style={{ 
          marginTop: '40px', 
          paddingTop: '24px', 
          borderTop: '1px solid var(--border-default)', 
          textAlign: 'center', 
          fontSize: '0.7rem', 
          color: 'var(--text-muted)',
          letterSpacing: '0.05em'
        }}>
          SYSTEM ID: FV-001 • SENTINEL OS v4.2.1
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
