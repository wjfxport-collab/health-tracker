import React, { useState, useEffect } from 'react';
import { X, Lock, User, Key, Fingerprint, ShieldCheck, ArrowRight, Sparkles, AlertCircle, CheckCircle2 } from 'lucide-react';
import { isBiometricAvailable, loginWithPasskey } from '../utils/webauthn';

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [hasBiometrics, setHasBiometrics] = useState(false);

  useEffect(() => {
    isBiometricAvailable().then(setHasBiometrics);
  }, []);

  if (!isOpen) return null;

  const handlePasswordAuth = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (isRegister && password !== confirmPassword) {
      setErrorMsg('Passwords do not match.');
      return;
    }

    setLoading(true);
    const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username.trim(),
          password: password.trim()
        })
      });

      const rawText = await res.text();
      let data = {};
      try {
        data = rawText ? JSON.parse(rawText) : {};
      } catch (parseErr) {
        throw new Error(`Server returned status ${res.status} (${res.statusText || 'No JSON response'}). Please ensure the backend server is running on port 5000.`);
      }

      if (!res.ok || !data.success) {
        throw new Error(data.error || `Authentication failed with status ${res.status}`);
      }

      onAuthSuccess(data.token, data.user);
      onClose();
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePasskeySignIn = async () => {
    setErrorMsg('');
    setLoading(true);
    try {
      const data = await loginWithPasskey(username.trim());
      onAuthSuccess(data.token, data.user);
      onClose();
    } catch (err) {
      console.error('Passkey sign in error:', err);
      setErrorMsg(err.message || 'Passkey authentication failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '440px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={20} style={{ color: 'var(--brand-primary)' }} />
            {isRegister ? 'Create HealthPulse Account' : 'Sign In to HealthPulse'}
          </h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Tab Switcher */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-light)', marginBottom: '20px' }}>
          <button
            type="button"
            onClick={() => { setIsRegister(false); setErrorMsg(''); }}
            style={{
              flex: 1,
              padding: '10px',
              background: 'none',
              border: 'none',
              borderBottom: !isRegister ? '2px solid var(--brand-primary)' : '2px solid transparent',
              fontWeight: 700,
              fontSize: '14px',
              color: !isRegister ? 'var(--brand-primary)' : 'var(--text-secondary)',
              cursor: 'pointer'
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsRegister(true); setErrorMsg(''); }}
            style={{
              flex: 1,
              padding: '10px',
              background: 'none',
              border: 'none',
              borderBottom: isRegister ? '2px solid var(--brand-primary)' : '2px solid transparent',
              fontWeight: 700,
              fontSize: '14px',
              color: isRegister ? 'var(--brand-primary)' : 'var(--text-secondary)',
              cursor: 'pointer'
            }}
          >
            Register
          </button>
        </div>

        {errorMsg && (
          <div style={{
            background: 'rgba(225, 29, 72, 0.08)',
            border: '1px solid rgba(225, 29, 72, 0.2)',
            borderRadius: '8px',
            padding: '10px 14px',
            marginBottom: '16px',
            fontSize: '13px',
            color: 'var(--brand-rose)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Biometric Passkey Quick Sign-in Button (if not registering) */}
        {!isRegister && (
          <div style={{ marginBottom: '18px' }}>
            <button
              type="button"
              className="btn"
              onClick={handlePasskeySignIn}
              disabled={loading}
              style={{
                width: '100%',
                background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                color: 'white',
                padding: '12px',
                fontSize: '14px',
                fontWeight: 700,
                borderRadius: '10px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.25)'
              }}
            >
              <Fingerprint size={18} />
              Sign in with Touch ID / Face ID / Passkey
            </button>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              margin: '18px 0',
              color: 'var(--text-muted)',
              fontSize: '12px'
            }}>
              <div style={{ flex: 1, height: '1px', background: 'var(--border-light)' }}></div>
              <span style={{ padding: '0 10px', textTransform: 'uppercase', fontWeight: 600 }}>or with password</span>
              <div style={{ flex: 1, height: '1px', background: 'var(--border-light)' }}></div>
            </div>
          </div>
        )}

        {/* Password Form */}
        <form onSubmit={handlePasswordAuth}>
          <div className="form-group">
            <label className="form-label" style={{ fontSize: '13px' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                <User size={14} /> Username
              </span>
            </label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. alex"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label" style={{ fontSize: '13px' }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                <Lock size={14} /> Password
              </span>
            </label>
            <input
              type="password"
              className="form-input"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {isRegister && (
            <div className="form-group">
              <label className="form-label" style={{ fontSize: '13px' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                  <Lock size={14} /> Confirm Password
                </span>
              </label>
              <input
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
          )}

          <div style={{ marginTop: '20px' }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: '100%', padding: '12px', fontSize: '14px', justifyContent: 'center' }}
            >
              {loading ? 'Authenticating...' : isRegister ? 'Create Account' : 'Sign In'}
              <ArrowRight size={16} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
