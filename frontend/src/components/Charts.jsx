import React, { useState } from 'react';
import { TrendingDown, BarChart2 } from 'lucide-react';

export default function Charts({ entries, goals }) {
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const [hoveredBar, setHoveredBar] = useState(null);

  const unit = goals?.weight_unit || 'lbs';
  const stepGoal = goals?.daily_steps_goal || 10000;
  const targetWeight = goals?.target_weight || 165;

  // Entries are newest first, reverse for chronological charts (last 14-30 entries)
  const chronological = [...entries].reverse().slice(-14);

  if (chronological.length === 0) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
        <p style={{ color: 'var(--text-muted)' }}>No data to plot yet. Add your first entry!</p>
      </div>
    );
  }

  // --- Weight Chart Calculations ---
  const weightData = chronological.filter(e => e.weight !== null && e.weight !== undefined);
  const minWeight = Math.min(...weightData.map(d => d.weight), targetWeight) - 2;
  const maxWeight = Math.max(...weightData.map(d => d.weight), targetWeight) + 2;
  const weightRange = maxWeight - minWeight || 1;

  const chartWidth = 500;
  const chartHeight = 160;
  const paddingX = 40;
  const paddingY = 20;

  const getWeightX = (idx, total) => paddingX + (idx / Math.max(1, total - 1)) * (chartWidth - paddingX * 2);
  const getWeightY = (w) => chartHeight - paddingY - ((w - minWeight) / weightRange) * (chartHeight - paddingY * 2);

  const weightPoints = weightData.map((d, i) => ({
    x: getWeightX(i, weightData.length),
    y: getWeightY(d.weight),
    ...d
  }));

  const weightPolyline = weightPoints.map(p => `${p.x},${p.y}`).join(' ');
  const targetY = getWeightY(targetWeight);

  // --- Steps Chart Calculations ---
  const maxSteps = Math.max(...chronological.map(d => d.steps || 0), stepGoal) * 1.15 || 12000;
  const barGap = 6;
  const availableWidth = chartWidth - paddingX * 2;
  const barWidth = Math.max(8, (availableWidth / chronological.length) - barGap);

  const getBarHeight = (steps) => ((steps || 0) / maxSteps) * (chartHeight - paddingY * 2);
  const stepGoalY = chartHeight - paddingY - (stepGoal / maxSteps) * (chartHeight - paddingY * 2);

  return (
    <div className="charts-grid">
      {/* Weight Trend Chart */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">
              <TrendingDown size={18} style={{ color: 'var(--brand-primary)' }} />
              Weight Progression
            </h3>
            <span className="card-subtitle">Last 14 entries ({unit})</span>
          </div>
          <span className="badge badge-success">Target: {targetWeight} {unit}</span>
        </div>

        <div className="chart-container">
          <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="chart-svg">
            {/* Target Weight Line */}
            <line
              x1={paddingX}
              y1={targetY}
              x2={chartWidth - paddingX}
              y2={targetY}
              stroke="#059669"
              strokeDasharray="4 4"
              strokeWidth="1.5"
              opacity="0.6"
            />
            <text
              x={chartWidth - paddingX + 4}
              y={targetY + 4}
              fontSize="10"
              fill="#059669"
              fontWeight="600"
            >
              Goal
            </text>

            {/* Grid baseline lines */}
            <line
              x1={paddingX}
              y1={chartHeight - paddingY}
              x2={chartWidth - paddingX}
              y2={chartHeight - paddingY}
              stroke="var(--border-light)"
              strokeWidth="1"
            />

            {/* Weight Line */}
            {weightPoints.length > 1 && (
              <polyline
                fill="none"
                stroke="var(--brand-primary)"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={weightPolyline}
              />
            )}

            {/* Data Point Circles */}
            {weightPoints.map((p, idx) => (
              <g key={p.id || idx}>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={hoveredPoint?.id === p.id ? 6 : 4}
                  fill="#ffffff"
                  stroke="var(--brand-primary)"
                  strokeWidth="2.5"
                  style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
                  onMouseEnter={() => setHoveredPoint(p)}
                  onMouseLeave={() => setHoveredPoint(null)}
                />
                {/* Date labels for first, middle, last */}
                {(idx === 0 || idx === Math.floor(weightPoints.length / 2) || idx === weightPoints.length - 1) && (
                  <text
                    x={p.x}
                    y={chartHeight - 4}
                    fontSize="10"
                    textAnchor="middle"
                    fill="var(--text-muted)"
                    fontWeight="500"
                  >
                    {p.date.slice(5)}
                  </text>
                )}
              </g>
            ))}
          </svg>

          {/* Hover Tooltip */}
          {hoveredPoint && (
            <div
              style={{
                position: 'absolute',
                left: `${(hoveredPoint.x / chartWidth) * 100}%`,
                top: `${(hoveredPoint.y / chartHeight) * 100}%`,
                transform: 'translate(-50%, -120%)',
                background: 'var(--text-primary)',
                color: '#ffffff',
                padding: '4px 8px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: 600,
                pointerEvents: 'none',
                whiteSpace: 'nowrap',
                boxShadow: 'var(--shadow-md)',
                zIndex: 10
              }}
            >
              {hoveredPoint.date}: <strong>{hoveredPoint.weight} {unit}</strong>
            </div>
          )}
        </div>
      </div>

      {/* Daily Steps Bar Chart */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">
              <BarChart2 size={18} style={{ color: 'var(--brand-blue)' }} />
              Daily Step Activity
            </h3>
            <span className="card-subtitle">Daily count vs {stepGoal.toLocaleString()} goal</span>
          </div>
          <span className="badge badge-muted">Daily Goal: {stepGoal.toLocaleString()}</span>
        </div>

        <div className="chart-container">
          <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="chart-svg">
            {/* Step Goal Line */}
            <line
              x1={paddingX}
              y1={stepGoalY}
              x2={chartWidth - paddingX}
              y2={stepGoalY}
              stroke="#2563eb"
              strokeDasharray="4 4"
              strokeWidth="1.5"
              opacity="0.6"
            />
            <text
              x={chartWidth - paddingX + 4}
              y={stepGoalY + 4}
              fontSize="10"
              fill="#2563eb"
              fontWeight="600"
            >
              Goal
            </text>

            {/* Grid baseline */}
            <line
              x1={paddingX}
              y1={chartHeight - paddingY}
              x2={chartWidth - paddingX}
              y2={chartHeight - paddingY}
              stroke="var(--border-light)"
              strokeWidth="1"
            />

            {/* Step Bars */}
            {chronological.map((d, idx) => {
              const h = getBarHeight(d.steps);
              const x = paddingX + idx * (barWidth + barGap);
              const y = chartHeight - paddingY - h;
              const isGoalMet = (d.steps || 0) >= stepGoal;

              return (
                <g key={d.id || idx}>
                  <rect
                    x={x}
                    y={y}
                    width={barWidth}
                    height={Math.max(2, h)}
                    rx="3"
                    fill={isGoalMet ? 'var(--brand-primary)' : 'var(--brand-blue-border)'}
                    stroke={isGoalMet ? 'none' : 'var(--brand-blue)'}
                    strokeWidth={isGoalMet ? 0 : 1}
                    style={{ cursor: 'pointer', transition: 'opacity 0.15s' }}
                    opacity={hoveredBar?.id === d.id ? 0.8 : 1}
                    onMouseEnter={() => setHoveredBar({ ...d, x: x + barWidth / 2, y })}
                    onMouseLeave={() => setHoveredBar(null)}
                  />
                  {(idx === 0 || idx === Math.floor(chronological.length / 2) || idx === chronological.length - 1) && (
                    <text
                      x={x + barWidth / 2}
                      y={chartHeight - 4}
                      fontSize="10"
                      textAnchor="middle"
                      fill="var(--text-muted)"
                      fontWeight="500"
                    >
                      {d.date.slice(5)}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Bar Hover Tooltip */}
          {hoveredBar && (
            <div
              style={{
                position: 'absolute',
                left: `${(hoveredBar.x / chartWidth) * 100}%`,
                top: `${(hoveredBar.y / chartHeight) * 100}%`,
                transform: 'translate(-50%, -120%)',
                background: 'var(--text-primary)',
                color: '#ffffff',
                padding: '4px 8px',
                borderRadius: '6px',
                fontSize: '11px',
                fontWeight: 600,
                pointerEvents: 'none',
                whiteSpace: 'nowrap',
                boxShadow: 'var(--shadow-md)',
                zIndex: 10
              }}
            >
              {hoveredBar.date}: <strong>{(hoveredBar.steps || 0).toLocaleString()} steps</strong>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
