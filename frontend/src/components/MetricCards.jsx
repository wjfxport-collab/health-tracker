import React from 'react';
import { Scale, Footprints, Flame, TrendingDown, Target, Award } from 'lucide-react';

export default function MetricCards({ stats, goals, onOpenLogModal }) {
  if (!stats) return null;

  const unit = goals?.weight_unit || 'lbs';
  const stepGoal = goals?.daily_steps_goal || 10000;
  const todaySteps = stats.today_steps || 0;
  const stepPercent = Math.min(100, Math.round((todaySteps / stepGoal) * 100));

  const latestWeight = stats.latest_weight;
  const weightChange = stats.weight_change || 0;
  const isLoss = weightChange <= 0;

  return (
    <div className="metrics-grid">
      {/* Weight Card */}
      <div className="metric-card">
        <div>
          <div className="metric-top">
            <span className="metric-label">Latest Weight</span>
            <div className="metric-icon-wrap" style={{ background: 'var(--brand-primary-subtle)', color: 'var(--brand-primary)' }}>
              <Scale size={20} />
            </div>
          </div>
          <div className="metric-value-row">
            <span className="metric-value">{latestWeight ? latestWeight : '--'}</span>
            <span className="metric-unit">{unit}</span>
          </div>
          <div className="metric-sub">
            <span style={{ color: isLoss ? 'var(--brand-primary)' : 'var(--brand-rose)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
              <TrendingDown size={14} style={{ transform: isLoss ? 'none' : 'rotate(180deg)' }} />
              {Math.abs(weightChange)} {unit} {isLoss ? 'lost' : 'gained'}
            </span>
            <span>vs starting ({stats.starting_weight} {unit})</span>
          </div>
        </div>
        <div className="progress-bar-bg">
          <div 
            className="progress-bar-fill" 
            style={{ width: `${stats.progress_percent || 0}%`, background: 'var(--brand-primary)' }}
            title={`${stats.progress_percent}% towards target goal`}
          />
        </div>
      </div>

      {/* Steps Today Card */}
      <div className="metric-card">
        <div>
          <div className="metric-top">
            <span className="metric-label">Steps Today</span>
            <div className="metric-icon-wrap" style={{ background: 'var(--brand-blue-subtle)', color: 'var(--brand-blue)' }}>
              <Footprints size={20} />
            </div>
          </div>
          <div className="metric-value-row">
            <span className="metric-value">{todaySteps.toLocaleString()}</span>
            <span className="metric-unit">/ {stepGoal.toLocaleString()}</span>
          </div>
          <div className="metric-sub">
            {todaySteps >= stepGoal ? (
              <span style={{ color: 'var(--brand-primary)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Award size={14} /> Goal Achieved!
              </span>
            ) : (
              <span>{(stepGoal - todaySteps).toLocaleString()} steps remaining</span>
            )}
          </div>
        </div>
        <div className="progress-bar-bg">
          <div 
            className="progress-bar-fill" 
            style={{ 
              width: `${stepPercent}%`, 
              background: todaySteps >= stepGoal ? 'var(--brand-primary)' : 'var(--brand-blue)' 
            }} 
          />
        </div>
      </div>

      {/* 7-Day Average Card */}
      <div className="metric-card">
        <div>
          <div className="metric-top">
            <span className="metric-label">7-Day Average Steps</span>
            <div className="metric-icon-wrap" style={{ background: 'var(--brand-amber-subtle)', color: 'var(--brand-amber)' }}>
              <Flame size={20} />
            </div>
          </div>
          <div className="metric-value-row">
            <span className="metric-value">{(stats.avg_steps_7d || 0).toLocaleString()}</span>
            <span className="metric-unit">steps/day</span>
          </div>
          <div className="metric-sub">
            <span>30-Day Avg: {(stats.avg_steps_30d || 0).toLocaleString()}</span>
          </div>
        </div>
        <div className="metric-sub" style={{ marginTop: '12px', fontSize: '11px', color: 'var(--text-muted)' }}>
          Best Day: {(stats.best_step_day || 0).toLocaleString()} steps
        </div>
      </div>

      {/* Goal Streak Card */}
      <div className="metric-card">
        <div>
          <div className="metric-top">
            <span className="metric-label">Consistency</span>
            <div className="metric-icon-wrap" style={{ background: '#f5f3ff', color: '#7c3aed' }}>
              <Target size={20} />
            </div>
          </div>
          <div className="metric-value-row">
            <span className="metric-value">{stats.current_step_streak || 0}</span>
            <span className="metric-unit">day streak</span>
          </div>
          <div className="metric-sub">
            <span>{stats.days_goal_met || 0} total days goal reached</span>
          </div>
        </div>
        <div style={{ marginTop: '10px' }}>
          <button 
            className="btn btn-secondary btn-sm" 
            style={{ width: '100%', fontSize: '13px' }}
            onClick={onOpenLogModal}
          >
            + Log Today's Numbers
          </button>
        </div>
      </div>
    </div>
  );
}
