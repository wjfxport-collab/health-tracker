import React, { useState } from 'react';
import { Search, Edit2, Trash2, CheckCircle2, History, AlertCircle } from 'lucide-react';

export default function HistoryTable({ entries, goals, onEdit, onDelete }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);

  const unit = goals?.weight_unit || 'lbs';
  const stepGoal = goals?.daily_steps_goal || 10000;

  const filtered = entries.filter((e) => {
    const term = searchTerm.toLowerCase();
    return (
      e.date.toLowerCase().includes(term) ||
      (e.notes && e.notes.toLowerCase().includes(term))
    );
  });

  const handleDelete = async (id) => {
    await onDelete(id);
    setDeleteConfirmId(null);
  };

  return (
    <div className="card">
      <div className="card-header" style={{ flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 className="card-title">
            <History size={18} style={{ color: 'var(--text-secondary)' }} />
            Entry History & Logs
          </h3>
          <span className="card-subtitle">{entries.length} total logged days</span>
        </div>

        {/* Search Bar */}
        <div style={{ position: 'relative', minWidth: '220px' }}>
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '10px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)'
            }}
          />
          <input
            type="text"
            className="form-input"
            style={{ paddingLeft: '32px', fontSize: '13px' }}
            placeholder="Search date or note..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="table-responsive">
        <table className="tracker-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Weight</th>
              <th>Steps</th>
              <th>Goal Status</th>
              <th>Notes</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  No entries found matching your search.
                </td>
              </tr>
            ) : (
              filtered.map((entry) => {
                const isGoalMet = (entry.steps || 0) >= stepGoal;
                return (
                  <tr key={entry.id}>
                    <td style={{ fontWeight: 600 }}>{entry.date}</td>
                    <td>
                      {entry.weight !== null && entry.weight !== undefined ? (
                        <strong>{entry.weight} <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{unit}</span></strong>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>--</span>
                      )}
                    </td>
                    <td>
                      {entry.steps !== null && entry.steps !== undefined ? (
                        <span>{entry.steps.toLocaleString()}</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>--</span>
                      )}
                    </td>
                    <td>
                      {entry.steps !== null && entry.steps !== undefined ? (
                        isGoalMet ? (
                          <span className="badge badge-success">
                            <CheckCircle2 size={12} /> Met ({stepGoal.toLocaleString()})
                          </span>
                        ) : (
                          <span className="badge badge-muted">
                            {Math.round(((entry.steps || 0) / stepGoal) * 100)}% of goal
                          </span>
                        )
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>--</span>
                      )}
                    </td>
                    <td style={{ maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {entry.notes ? (
                        <span title={entry.notes}>{entry.notes}</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '12px' }}>No notes</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '6px', alignItems: 'center' }}>
                        {deleteConfirmId === entry.id ? (
                          <>
                            <span style={{ fontSize: '11px', color: 'var(--brand-rose)', fontWeight: 600 }}>Delete?</span>
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => handleDelete(entry.id)}
                            >
                              Yes
                            </button>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => setDeleteConfirmId(null)}
                            >
                              No
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              className="btn btn-secondary btn-sm"
                              style={{ padding: '4px 8px' }}
                              onClick={() => onEdit(entry)}
                              title="Edit entry"
                            >
                              <Edit2 size={13} />
                            </button>
                            <button
                              className="btn btn-danger btn-sm"
                              style={{ padding: '4px 8px' }}
                              onClick={() => setDeleteConfirmId(entry.id)}
                              title="Delete entry"
                            >
                              <Trash2 size={13} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
