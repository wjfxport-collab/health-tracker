import React, { useState, useEffect } from 'react';
import { X, Target, Save, Check, Sparkles, Eye, EyeOff, ExternalLink, Fingerprint, ShieldCheck, Trash2, Plus, LogOut, User } from 'lucide-react';
import { registerPasskey } from '../utils/webauthn';

export default function GoalSettings({ isOpen, onClose, goals, onSaveGoals, user, token, onLogout, onPasskeysChanged }) {
  const [stepGoal, setStepGoal] = useState(10000);
  const [targetWeight, setTargetWeight] = useState(165);
  const [startingWeight, setStartingWeight] = useState(185);
  const [unit, setUnit] = useState('lbs');
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  
  // Passkey enrollment state
  const [passkeyNickname, setPasskeyNickname] = useState('');
  const [registeringPasskey, setRegisteringPasskey] = useState(false);
  const [passkeyMsg, setPasskeyMsg] = useState('');

  const [loading, setLoading] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (goals) {
      setStepGoal(goals.daily_steps_goal || 10000);
      setTargetWeight(goals.target_weight || 165);
      setStartingWeight(goals.starting_weight || 185);
      setUnit(goals.weight_unit || 'lbs');
      setGeminiApiKey(goals.gemini_api_key || '');
    }
    setSavedSuccess(false);
    setPasskeyMsg('');
  }, [goals, isOpen]);

  if (!isOpen) return null;

  const handleRegisterPasskey = async () => {
    setRegisteringPasskey(true);
    setPasskeyMsg('');
    try {
      await registerPasskey(token, passkeyNickname || 'My Device Biometrics');
      setPasskeyMsg('✅ Biometric Passkey successfully enrolled!');
      setPasskeyNickname('');
      if (onPasskeysChanged) onPasskeysChanged();
    } catch (err) {
      setPasskeyMsg('❌ ' + (err.message || 'Passkey enrollment failed.'));
    } finally {
      setRegisteringPasskey(false);
    }
  };

  const handleDeletePasskey = async (credId) => {
    if (!window.confirm('Remove this passkey?')) return;
    try {
      const res = await fetch(`/api/auth/webauthn/credentials/${credId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success && onPasskeysChanged) {
        onPasskeysChanged();
      }
    } catch (err) {
      alert('Failed to remove passkey: ' + err.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSaveGoals({
        daily_steps_goal: parseInt(stepGoal, 10),
        target_weight: parseFloat(targetWeight),
        starting_weight: parseFloat(startingWeight),
        weight_unit: unit,
        gemini_api_key: geminiApiKey.trim()
      });
      setSavedSuccess(true);
      setTimeout(() => {
        onClose();
      }, 700);
    } catch (err) {
      alert('Error updating settings: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '560px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Target size={20} style={{ color: 'var(--brand-primary)' }} />
            Account & Goal Settings
          </h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* User Account Bar */}
        {user && (
          <div style={{
            background: 'var(--bg-subtle)',
            border: '1px solid var(--border-light)',
            borderRadius: '8px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '18px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                background: 'var(--brand-primary)',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: '14px'
              }}>
                {user.username?.[0]?.toUpperCase() || 'U'}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
                  {user.username}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  User #{user.id} • Private Account
                </div>
              </div>
            </div>

            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => { onClose(); onLogout(); }}
            >
              <LogOut size={13} /> Sign Out
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Biometrics & Passkeys Section */}
          <div style={{
            background: '#f8fafc',
            border: '1px solid var(--border-medium)',
            borderRadius: 'var(--radius-md)',
            padding: '14px',
            marginBottom: '18px'
          }}>
            <h4 style={{ fontSize: '13px', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
              <Fingerprint size={16} style={{ color: '#6366f1' }} />
              Biometric Passkeys (Face ID / Touch ID)
            </h4>

            <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.4, marginBottom: '10px' }}>
              Register this device's fingerprint or face scan for instant passwordless sign-in.
            </p>

            {/* List of enrolled passkeys */}
            {user?.passkeys && user.passkeys.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '10px' }}>
                {user.passkeys.map((pk) => (
                  <div key={pk.id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: '#ffffff',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: '1px solid var(--border-light)',
                    fontSize: '12px'
                  }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                      <ShieldCheck size={14} style={{ color: 'var(--brand-primary)' }} />
                      {pk.nickname || 'Biometric Passkey'}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDeletePasskey(pk.id)}
                      style={{ background: 'none', border: 'none', color: 'var(--brand-rose)', cursor: 'pointer', padding: '4px' }}
                      title="Remove passkey"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Register new passkey */}
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                className="form-input"
                style={{ fontSize: '12px', padding: '6px 10px' }}
                placeholder="Device Name (e.g. MacBook Touch ID)"
                value={passkeyNickname}
                onChange={(e) => setPasskeyNickname(e.target.value)}
              />
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={handleRegisterPasskey}
                disabled={registeringPasskey}
                style={{ flexShrink: 0 }}
              >
                <Plus size={13} />
                {registeringPasskey ? 'Enrolling...' : 'Enroll Biometrics'}
              </button>
            </div>

            {passkeyMsg && (
              <div style={{ fontSize: '11px', marginTop: '6px', fontWeight: 600 }}>
                {passkeyMsg}
              </div>
            )}
          </div>

          {/* Fitness Targets Section */}
          <div style={{ marginBottom: '18px' }}>
            <h4 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>
              Fitness Targets
            </h4>

            {/* Weight Unit */}
            <div className="form-group" style={{ marginBottom: '10px' }}>
              <label className="form-label" style={{ fontSize: '12px' }}>Preferred Unit</label>
              <div style={{ display: 'flex', gap: '16px' }}>
                <label style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '13px' }}>
                  <input
                    type="radio"
                    name="unit"
                    value="lbs"
                    checked={unit === 'lbs'}
                    onChange={(e) => setUnit(e.target.value)}
                  />
                  Pounds (lbs)
                </label>
                <label style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '13px' }}>
                  <input
                    type="radio"
                    name="unit"
                    value="kg"
                    checked={unit === 'kg'}
                    onChange={(e) => setUnit(e.target.value)}
                  />
                  Kilograms (kg)
                </label>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div className="form-group" style={{ marginBottom: '10px' }}>
                <label className="form-label" style={{ fontSize: '12px' }}>Daily Step Goal</label>
                <input
                  type="number"
                  step="500"
                  className="form-input"
                  value={stepGoal}
                  onChange={(e) => setStepGoal(e.target.value)}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: '10px' }}>
                <label className="form-label" style={{ fontSize: '12px' }}>Target Weight ({unit})</label>
                <input
                  type="number"
                  step="0.1"
                  className="form-input"
                  value={targetWeight}
                  onChange={(e) => setTargetWeight(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: '0' }}>
              <label className="form-label" style={{ fontSize: '12px' }}>Starting Weight ({unit})</label>
              <input
                type="number"
                step="0.1"
                className="form-input"
                value={startingWeight}
                onChange={(e) => setStartingWeight(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Gemini AI Vision Key Section */}
          <div style={{
            background: 'var(--brand-purple-subtle)',
            border: '1px solid var(--brand-purple-border)',
            borderRadius: 'var(--radius-md)',
            padding: '14px',
            marginBottom: '20px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <h4 style={{ fontSize: '12px', fontWeight: 800, color: 'var(--brand-purple)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={14} />
                Google Gemini Flash Vision API Key
              </h4>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noreferrer"
                style={{ fontSize: '11px', color: 'var(--brand-purple)', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '3px' }}
              >
                Get Free Key <ExternalLink size={10} />
              </a>
            </div>

            <div style={{ position: 'relative' }}>
              <input
                type={showApiKey ? 'text' : 'password'}
                placeholder="AIzaSy..."
                className="form-input"
                style={{ paddingRight: '40px', fontSize: '13px', background: '#ffffff' }}
                value={geminiApiKey}
                onChange={(e) => setGeminiApiKey(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-muted)'
                }}
              >
                {showApiKey ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading || savedSuccess}>
              {savedSuccess ? (
                <>
                  <Check size={16} /> Saved!
                </>
              ) : (
                <>
                  <Save size={16} /> {loading ? 'Saving...' : 'Save Settings'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
