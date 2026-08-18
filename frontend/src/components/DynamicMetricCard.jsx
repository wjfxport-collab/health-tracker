import React from 'react';
import { getPluginIcon, getCategoryBadgeColor } from '../utils/pluginRegistry';
import { TrendingDown, Award, Plus, Calendar, Clock } from 'lucide-react';

export default function DynamicMetricCard({ plugin, data, onOpenLogModal }) {
  if (!plugin) return null;

  const manifest = plugin.manifest || plugin;
  const stats = data?.stats || {};
  const isEquipment = manifest.category === 'equipment' || manifest.visualizations?.cardType === 'log_summary';
  const badgeStyle = getCategoryBadgeColor(manifest.category);
  const color = manifest.color || '#059669';

  // 1. Equipment / Session Log Card (e.g. Camera & Lens Gear Tracker)
  if (isEquipment) {
    const totalSessions = stats.total_sessions || 0;
    const latestSession = stats.latest_session;
    const topCamera = stats.top_camera || 'None';
    const topLens = stats.top_lens || 'None';

    return (
      <div className="metric-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          <div className="metric-top">
            <span className="metric-label">{manifest.name}</span>
            <div className="metric-icon-wrap" style={{ background: `${color}15`, color }}>
              {getPluginIcon(manifest.icon, { size: 20 })}
            </div>
          </div>

          <div className="metric-value-row">
            <span className="metric-value">{totalSessions}</span>
            <span className="metric-unit">sessions logged</span>
          </div>

          <div className="metric-sub" style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Top Body:</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{topCamera}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Top Lens:</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{topLens}</span>
            </div>
            {latestSession && (
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                <span>Latest Shoot:</span>
                <span>{latestSession.timedate_of_use ? new Date(latestSession.timedate_of_use).toLocaleDateString() : 'Recent'}</span>
              </div>
            )}
          </div>
        </div>

        <div style={{ marginTop: '16px' }}>
          <button
            className="btn btn-secondary btn-sm"
            style={{ width: '100%', fontSize: '13px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
            onClick={() => onOpenLogModal(manifest.id)}
          >
            <Plus size={14} /> Log Gear Session
          </button>
        </div>
      </div>
    );
  }

  // 2. Numeric Health & Activity Card (Weight, Steps, etc.)
  const primaryField = manifest.fields?.[0] || {};
  const unit = primaryField.unit || '';
  const latestValue = stats.latest_value;
  const targetGoal = stats.target_goal;
  const progressPercent = targetGoal && latestValue ? Math.min(100, Math.round((latestValue / targetGoal) * 100)) : 0;

  return (
    <div className="metric-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <div>
        <div className="metric-top">
          <span className="metric-label">{manifest.name}</span>
          <div className="metric-icon-wrap" style={{ background: `${color}15`, color }}>
            {getPluginIcon(manifest.icon, { size: 20 })}
          </div>
        </div>

        <div className="metric-value-row">
          <span className="metric-value">{latestValue !== null && latestValue !== undefined ? Number(latestValue).toLocaleString() : '--'}</span>
          {unit && <span className="metric-unit">{unit}</span>}
        </div>

        <div className="metric-sub" style={{ marginTop: '8px' }}>
          {stats.streak > 0 ? (
            <span style={{ color: 'var(--brand-primary)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Award size={14} /> {stats.streak} day streak!
            </span>
          ) : (
            <span>7-Day Avg: {stats.avg_7d ? Number(stats.avg_7d).toLocaleString() : '0'} {unit}</span>
          )}
        </div>
      </div>

      <div style={{ marginTop: '16px' }}>
        {targetGoal && (
          <div className="progress-bar-bg" style={{ marginBottom: '12px' }}>
            <div
              className="progress-bar-fill"
              style={{ width: `${progressPercent}%`, background: color }}
              title={`Target: ${targetGoal} ${unit}`}
            />
          </div>
        )}
        <button
          className="btn btn-secondary btn-sm"
          style={{ width: '100%', fontSize: '13px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
          onClick={() => onOpenLogModal(manifest.id)}
        >
          <Plus size={14} /> Log {manifest.name}
        </button>
      </div>
    </div>
  );
}
