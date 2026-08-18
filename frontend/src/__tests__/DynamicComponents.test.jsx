import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DynamicMetricCard from '../components/DynamicMetricCard';
import DynamicLogModal from '../components/DynamicLogModal';
import DynamicHistoryTable from '../components/DynamicHistoryTable';

describe('Dynamic Metric Components', () => {
  const mockCameraPlugin = {
    id: 'camera_log',
    name: 'Camera & Lens Gear Log',
    category: 'equipment',
    icon: 'Camera',
    color: '#4f46e5',
    manifest: {
      id: 'camera_log',
      name: 'Camera & Lens Gear Log',
      category: 'equipment',
      icon: 'Camera',
      color: '#4f46e5',
      fields: [
        { id: 'camera_body', label: 'Camera Body', type: 'select', required: true, options: ['Sony A7 IV', 'Canon EOS R5'] },
        { id: 'lens', label: 'Lens Used', type: 'text', required: true },
        { id: 'timedate_of_use', label: 'Date & Time of Session', type: 'datetime-local', required: true },
        { id: 'aperture', label: 'Aperture', type: 'select', required: false, options: ['f/1.4', 'f/2.8'] },
        { id: 'comment', label: 'Shoot Notes', type: 'textarea', required: false }
      ],
      visualizations: { cardType: 'log_summary' }
    }
  };

  const mockWeightPlugin = {
    id: 'weight',
    name: 'Weight Tracker',
    category: 'body_composition',
    icon: 'Scale',
    color: '#059669',
    manifest: {
      id: 'weight',
      name: 'Weight Tracker',
      category: 'body_composition',
      icon: 'Scale',
      color: '#059669',
      fields: [
        { id: 'weight', label: 'Weight', type: 'number', required: true, unit: 'lbs' }
      ],
      goals: { defaultTarget: 165.0 }
    }
  };

  it('renders numeric card with latest value and 7-day average', () => {
    const data = {
      stats: {
        latest_value: 176.4,
        avg_7d: 177.2,
        streak: 5,
        target_goal: 165.0
      }
    };

    render(<DynamicMetricCard plugin={mockWeightPlugin} data={data} onOpenLogModal={() => {}} />);

    expect(screen.getByText('Weight Tracker')).toBeInTheDocument();
    expect(screen.getByText('176.4')).toBeInTheDocument();
    expect(screen.getByText(/5 day streak/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Log Weight Tracker/i })).toBeInTheDocument();
  });

  it('renders equipment session card with top camera and top lens', () => {
    const data = {
      stats: {
        total_sessions: 14,
        top_camera: 'Sony A7 IV',
        top_lens: 'FE 24-70mm f/2.8 GM II',
        latest_session: {
          camera_body: 'Sony A7 IV',
          lens: 'FE 24-70mm f/2.8 GM II',
          timedate_of_use: '2026-08-18T14:30'
        }
      }
    };

    render(<DynamicMetricCard plugin={mockCameraPlugin} data={data} onOpenLogModal={() => {}} />);

    expect(screen.getByText('Camera & Lens Gear Log')).toBeInTheDocument();
    expect(screen.getByText('14')).toBeInTheDocument();
    expect(screen.getByText('sessions logged')).toBeInTheDocument();
    expect(screen.getByText('Sony A7 IV')).toBeInTheDocument();
    expect(screen.getByText('FE 24-70mm f/2.8 GM II')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Log Gear Session/i })).toBeInTheDocument();
  });

  it('renders DynamicLogModal with fields generated from manifest', () => {
    render(
      <DynamicLogModal
        isOpen={true}
        onClose={() => {}}
        plugins={[mockWeightPlugin, mockCameraPlugin]}
        initialMetricId="camera_log"
      />
    );

    expect(screen.getByText(/Log Camera & Lens Gear Log/i)).toBeInTheDocument();
    expect(screen.getByText(/Camera Body/i)).toBeInTheDocument();
    expect(screen.getByText(/Lens Used/i)).toBeInTheDocument();
    expect(screen.getByText(/Date & Time of Session/i)).toBeInTheDocument();
    expect(screen.getByText(/Aperture/i)).toBeInTheDocument();
    expect(screen.getByText(/Shoot Notes/i)).toBeInTheDocument();
  });

  it('renders DynamicHistoryTable with filter tabs and entry details', () => {
    const mockEntries = [
      {
        id: 1,
        metric_id: 'camera_log',
        date: '2026-08-18',
        payload: { camera_body: 'Sony A7 IV', lens: '50mm f/1.2', focal_length: 50, aperture: 'f/1.4' },
        notes: 'Studio shoot'
      },
      {
        id: 2,
        metric_id: 'weight',
        date: '2026-08-18',
        payload: { weight: 175.4 },
        notes: 'Morning weigh-in'
      }
    ];

    render(
      <DynamicHistoryTable
        plugins={[mockWeightPlugin, mockCameraPlugin]}
        metricEntries={mockEntries}
      />
    );

    expect(screen.getByText(/Activity & Gear History/i)).toBeInTheDocument();
    expect(screen.getByText('Sony A7 IV')).toBeInTheDocument();
    expect(screen.getByText('50mm f/1.2')).toBeInTheDocument();
    expect(screen.getByText('175.4 lbs')).toBeInTheDocument();
    expect(screen.getByText('Studio shoot')).toBeInTheDocument();
  });
});
