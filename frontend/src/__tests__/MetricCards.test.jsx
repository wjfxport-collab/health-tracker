import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MetricCards from '../components/MetricCards';

describe('MetricCards Component', () => {
  const mockStats = {
    latest_weight: 175.4,
    starting_weight: 185.0,
    target_weight: 165.0,
    weight_change: -9.6,
    weight_unit: 'lbs',
    progress_percent: 48.0,
    today_steps: 11450,
    avg_steps_7d: 10800,
    avg_steps_30d: 9900,
    best_step_day: 14200,
    current_step_streak: 7,
    days_goal_met: 18,
    total_days_logged: 24
  };

  const mockGoals = {
    daily_steps_goal: 10000,
    target_weight: 165.0,
    starting_weight: 185.0,
    weight_unit: 'lbs'
  };

  it('renders key metric values correctly', () => {
    render(<MetricCards stats={mockStats} goals={mockGoals} />);

    expect(screen.getByText('175.4')).toBeInTheDocument();
    expect(screen.getByText('Latest Weight')).toBeInTheDocument();

    expect(screen.getByText('11,450')).toBeInTheDocument();
    expect(screen.getByText('Steps Today')).toBeInTheDocument();

    expect(screen.getByText('10,800')).toBeInTheDocument();
    expect(screen.getByText('7-Day Average Steps')).toBeInTheDocument();

    expect(screen.getByText('7')).toBeInTheDocument();
    expect(screen.getByText('day streak')).toBeInTheDocument();
  });

  it('renders weight change and goal achievement', () => {
    render(<MetricCards stats={mockStats} goals={mockGoals} />);

    expect(screen.getByText(/9.6 lbs lost/i)).toBeInTheDocument();
    expect(screen.getByText(/Goal Achieved!/i)).toBeInTheDocument();
    expect(screen.getByText(/18 total days goal reached/i)).toBeInTheDocument();
  });

  it('renders nothing when stats is null', () => {
    const { container } = render(<MetricCards stats={null} goals={mockGoals} />);
    expect(container.firstChild).toBeNull();
  });
});
