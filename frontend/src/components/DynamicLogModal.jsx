import React, { useState, useEffect } from 'react';
import { X, Check, AlertCircle, Sparkles } from 'lucide-react';
import { getPluginIcon } from '../utils/pluginRegistry';

export default function DynamicLogModal({
  isOpen,
  onClose,
  plugins = [],
  initialMetricId = 'weight',
  onEntrySaved
}) {
  const [activeMetricId, setActiveMetricId] = useState(initialMetricId);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [formData, setFormData] = useState({});
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Set default active metric when modal opens
  useEffect(() => {
    if (isOpen) {
      setActiveMetricId(initialMetricId || (plugins[0]?.id || 'weight'));
      setDate(new Date().toISOString().split('T')[0]);
      setError('');
      setSuccessMsg('');
    }
  }, [isOpen, initialMetricId, plugins]);

  // Reset form fields when active tab changes
  useEffect(() => {
    const currentPlugin = plugins.find(p => p.id === activeMetricId);
    if (!currentPlugin) return;

    const initialData = {};
    currentPlugin.manifest?.fields?.forEach(f => {
      if (f.type === 'datetime-local') {
        const now = new Date();
        const localIso = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
        initialData[f.id] = localIso;
      } else if (f.type === 'select' && f.options?.length) {
        initialData[f.id] = f.options[0];
      } else {
        initialData[f.id] = '';
      }
    });
    setFormData(initialData);
    setError('');
  }, [activeMetricId, plugins]);

  if (!isOpen) return null;

  const currentPlugin = plugins.find(p => p.id === activeMetricId) || plugins[0];
  const manifest = currentPlugin?.manifest || currentPlugin || {};
  const fields = manifest.fields || [];

  const handleFieldChange = (fieldId, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldId]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccessMsg('');

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/metrics/${activeMetricId}/entries`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          date,
          payload: formData,
          notes
        })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Failed to save entry.');
      }

      setSuccessMsg(`Successfully saved ${manifest.name}!`);
      if (onEntrySaved) onEntrySaved();
      setTimeout(() => {
        onClose();
      }, 700);
    } catch (err) {
      setError(err.message || 'An error occurred while saving.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '560px' }} onClick={e => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <h3 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {getPluginIcon(manifest.icon, { size: 20, style: { color: manifest.color || 'var(--brand-primary)' } })}
            Log {manifest.name}
          </h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Plugin Tabs */}
        {plugins.length > 1 && (
          <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-light)', paddingBottom: '12px', marginBottom: '16px', overflowX: 'auto' }}>
            {plugins.map(p => {
              const pManifest = p.manifest || p;
              const isActive = p.id === activeMetricId;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setActiveMetricId(p.id)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: '8px',
                    border: 'none',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    background: isActive ? (pManifest.color || 'var(--brand-primary)') : '#f1f5f9',
                    color: isActive ? '#ffffff' : 'var(--text-secondary)',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {getPluginIcon(pManifest.icon, { size: 14 })}
                  {pManifest.name}
                </button>
              );
            })}
          </div>
        )}

        {/* Error / Success Messages */}
        {error && (
          <div className="alert-box" style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', marginBottom: '16px' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="alert-box" style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', color: '#166534', marginBottom: '16px' }}>
            <Check size={16} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Dynamic Form Controls */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div className="form-group">
            <label className="form-label">Date</label>
            <input
              type="date"
              className="form-input"
              value={date}
              onChange={e => setDate(e.target.value)}
              required
            />
          </div>

          {fields.map(field => {
            const val = formData[field.id] ?? '';

            if (field.type === 'select') {
              return (
                <div key={field.id} className="form-group">
                  <label className="form-label">
                    {field.label} {field.required && <span style={{ color: '#ef4444' }}>*</span>}
                  </label>
                  <select
                    className="form-input"
                    value={val}
                    onChange={e => handleFieldChange(field.id, e.target.value)}
                    required={field.required}
                  >
                    {field.options?.map(opt => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                </div>
              );
            }

            if (field.type === 'textarea') {
              return (
                <div key={field.id} className="form-group">
                  <label className="form-label">
                    {field.label} {field.required && <span style={{ color: '#ef4444' }}>*</span>}
                  </label>
                  <textarea
                    className="form-input"
                    rows={3}
                    placeholder={field.placeholder || ''}
                    value={val}
                    onChange={e => handleFieldChange(field.id, e.target.value)}
                    required={field.required}
                  />
                </div>
              );
            }

            return (
              <div key={field.id} className="form-group">
                <label className="form-label">
                  {field.label} {field.unit ? `(${field.unit})` : ''} {field.required && <span style={{ color: '#ef4444' }}>*</span>}
                </label>
                <input
                  type={field.type === 'number' || field.type === 'integer' ? 'number' : field.type || 'text'}
                  step={field.step || (field.type === 'integer' ? '1' : 'any')}
                  min={field.min}
                  max={field.max}
                  className="form-input"
                  placeholder={field.placeholder || ''}
                  value={val}
                  onChange={e => handleFieldChange(field.id, e.target.value)}
                  required={field.required}
                />
              </div>
            );
          })}

          <div className="form-group">
            <label className="form-label">Additional Notes</label>
            <input
              type="text"
              className="form-input"
              placeholder="Any extra context for this entry..."
              value={notes}
              onChange={e => setNotes(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
            <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={loading}>
              {loading ? 'Saving...' : `Save ${manifest.name}`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
