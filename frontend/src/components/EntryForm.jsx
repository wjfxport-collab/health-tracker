import React, { useState, useEffect } from 'react';
import { X, Calendar, Scale, Footprints, FileText, Check } from 'lucide-react';

export default function EntryForm({ isOpen, onClose, onSave, editingEntry, unit }) {
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [weight, setWeight] = useState('');
  const [steps, setSteps] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (editingEntry) {
      setDate(editingEntry.date || '');
      setWeight(editingEntry.weight !== null && editingEntry.weight !== undefined ? editingEntry.weight : '');
      setSteps(editingEntry.steps !== null && editingEntry.steps !== undefined ? editingEntry.steps : '');
      setNotes(editingEntry.notes || '');
    } else {
      setDate(new Date().toISOString().split('T')[0]);
      setWeight('');
      setSteps('');
      setNotes('');
    }
    setError('');
  }, [editingEntry, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!date) {
      setError('Please select a date.');
      return;
    }

    if (weight === '' && steps === '') {
      setError('Please enter at least weight or steps.');
      return;
    }

    setLoading(true);
    try {
      await onSave({
        id: editingEntry?.id,
        date,
        weight: weight !== '' ? parseFloat(weight) : null,
        steps: steps !== '' ? parseInt(steps, 10) : null,
        notes
      });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to save entry.');
    } finally {
      setLoading(false);
    }
  };

  const addSteps = (amount) => {
    const current = parseInt(steps, 10) || 0;
    setSteps(current + amount);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">
            {editingEntry ? 'Edit Health Entry' : 'Log Daily Weight & Steps'}
          </h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ padding: '10px 14px', background: 'var(--brand-rose-subtle)', color: 'var(--brand-rose)', borderRadius: '8px', fontSize: '13px', marginBottom: '16px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Date Picker */}
          <div className="form-group">
            <label className="form-label">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                <Calendar size={15} /> Date
              </span>
            </label>
            <input
              type="date"
              className="form-input"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </div>

          {/* Weight */}
          <div className="form-group">
            <label className="form-label">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                <Scale size={15} /> Weight ({unit || 'lbs'})
              </span>
            </label>
            <input
              type="number"
              step="0.1"
              placeholder="e.g. 175.4"
              className="form-input"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
            />
          </div>

          {/* Steps */}
          <div className="form-group">
            <label className="form-label">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                <Footprints size={15} /> Steps Count
              </span>
            </label>
            <input
              type="number"
              step="1"
              placeholder="e.g. 10450"
              className="form-input"
              value={steps}
              onChange={(e) => setSteps(e.target.value)}
            />
            {/* Quick step increment chips */}
            <div className="quick-steps-row">
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', alignSelf: 'center' }}>Quick add:</span>
              <button type="button" className="quick-step-chip" onClick={() => addSteps(1000)}>+1,000</button>
              <button type="button" className="quick-step-chip" onClick={() => addSteps(2500)}>+2,500</button>
              <button type="button" className="quick-step-chip" onClick={() => addSteps(5000)}>+5,000</button>
              <button type="button" className="quick-step-chip" onClick={() => setSteps(10000)}>10,000</button>
            </div>
          </div>

          {/* Notes */}
          <div className="form-group">
            <label className="form-label">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                <FileText size={15} /> Notes / Activity (optional)
              </span>
            </label>
            <input
              type="text"
              placeholder="e.g. Morning jog, leg day, felt energetic"
              className="form-input"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '24px' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <Check size={16} />
              {loading ? 'Saving...' : editingEntry ? 'Update Entry' : 'Save Entry'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
