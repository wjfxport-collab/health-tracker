import React, { useState } from 'react';
import { getPluginIcon } from '../utils/pluginRegistry';
import { Calendar, Trash2, Camera, Scale, Footprints, Layers } from 'lucide-react';

export default function DynamicHistoryTable({
  plugins = [],
  metricEntries = [],
  onDeleteEntry
}) {
  const [selectedPluginId, setSelectedPluginId] = useState('all');

  const filteredEntries = selectedPluginId === 'all'
    ? metricEntries
    : metricEntries.filter(e => e.metric_id === selectedPluginId);

  return (
    <div className="table-container" style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <h3 className="section-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={18} style={{ color: 'var(--brand-primary)' }} />
          Activity & Gear History
        </h3>

        {/* Filter Pills */}
        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto' }}>
          <button
            className={`btn btn-sm ${selectedPluginId === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSelectedPluginId('all')}
          >
            All Logs ({metricEntries.length})
          </button>
          {plugins.map(p => {
            const m = p.manifest || p;
            const count = metricEntries.filter(e => e.metric_id === p.id).length;
            return (
              <button
                key={p.id}
                className={`btn btn-sm ${selectedPluginId === p.id ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setSelectedPluginId(p.id)}
                style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
              >
                {getPluginIcon(m.icon, { size: 13 })}
                {m.name} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {filteredEntries.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
          <Layers size={36} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
          <p style={{ fontWeight: 600, fontSize: '15px' }}>No entries found.</p>
          <p style={{ fontSize: '13px' }}>Start logging above to build your timeline.</p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Metric / Type</th>
                <th>Primary Details</th>
                <th>Settings / Secondary</th>
                <th>Notes</th>
                <th style={{ width: '40px' }}></th>
              </tr>
            </thead>
            <tbody>
              {filteredEntries.map(entry => {
                const plugin = plugins.find(p => p.id === entry.metric_id);
                const manifest = plugin?.manifest || plugin || {};
                const p = entry.payload || {};

                return (
                  <tr key={entry.id}>
                    <td style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>
                      {entry.date}
                    </td>
                    <td>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '5px',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontSize: '12px',
                          fontWeight: 700,
                          background: `${manifest.color || '#64748b'}15`,
                          color: manifest.color || '#64748b'
                        }}
                      >
                        {getPluginIcon(manifest.icon, { size: 12 })}
                        {manifest.name || entry.metric_id}
                      </span>
                    </td>
                    <td>
                      {entry.metric_id === 'camera_log' ? (
                        <div>
                          <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{p.camera_body || '--'}</div>
                          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{p.lens || '--'}</div>
                        </div>
                      ) : entry.metric_id === 'weight' ? (
                        <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
                          {p.weight ? `${p.weight} lbs` : '--'}
                        </span>
                      ) : entry.metric_id === 'steps' ? (
                        <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
                          {p.steps ? `${Number(p.steps).toLocaleString()} steps` : '--'}
                        </span>
                      ) : (
                        <span style={{ fontWeight: 600 }}>{JSON.stringify(p)}</span>
                      )}
                    </td>
                    <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {entry.metric_id === 'camera_log' ? (
                        <span>
                          {[p.focal_length ? `${p.focal_length}mm` : null, p.aperture, p.iso ? `ISO ${p.iso}` : null, p.shutter_speed]
                            .filter(Boolean)
                            .join(' • ') || '--'}
                        </span>
                      ) : (
                        <span>--</span>
                      )}
                    </td>
                    <td style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                      {entry.notes || p.comment || '--'}
                    </td>
                    <td>
                      {onDeleteEntry && (
                        <button
                          className="btn-icon"
                          style={{ color: '#ef4444', padding: '4px' }}
                          title="Delete entry"
                          onClick={() => onDeleteEntry(entry.id)}
                        >
                          <Trash2 size={15} />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
