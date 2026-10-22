import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Overview } from '../pages/Overview';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    getStats: vi.fn(),
    getHistory: vi.fn(),
  },
}));

describe('Overview Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    (api.getStats as any).mockReturnValue(new Promise(() => {}));
    (api.getHistory as any).mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter>
        <Overview />
      </MemoryRouter>
    );

    expect(screen.getByText(/ACQUIRING NEURAL METRICS & AUDIT LOGS/i)).toBeInTheDocument();
  });

  it('renders error state when API is unavailable', async () => {
    (api.getStats as any).mockRejectedValue(
      new Error('Backend unavailable. Start the NØX FastAPI server to enable detection.')
    );
    (api.getHistory as any).mockRejectedValue(
      new Error('Backend unavailable. Start the NØX FastAPI server to enable detection.')
    );

    render(
      <MemoryRouter>
        <Overview />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText(/Backend unavailable. Start the NØX FastAPI server to enable detection./i)
      ).toBeInTheDocument();
    });

    expect(screen.getByText(/RETRY CONNECTION/i)).toBeInTheDocument();
  });

  it('renders metric cards with real backend telemetry', async () => {
    (api.getStats as any).mockResolvedValue({
      total_records_analyzed: 4500,
      predicted_normal_count: 3200,
      predicted_malicious_count: 1300,
      attack_percentage: 28.89,
      severity_distribution: {
        Normal: 3200,
        Low: 200,
        Medium: 600,
        High: 500,
      },
      most_recent_detection_timestamp: '2026-10-22T20:00:00Z',
    });

    (api.getHistory as any).mockResolvedValue([
      {
        id: 1,
        timestamp: '2026-10-22T20:00:00Z',
        prediction: 'Malicious',
        class_id: 1,
        attack_score: 0.942,
        threshold: 0.5,
        severity: 'High',
        model_version: 'NØX-MLP-v1',
        source_type: 'csv_upload',
      },
    ]);

    render(
      <MemoryRouter>
        <Overview />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('4,500')).toBeInTheDocument();
      expect(screen.getByText('1,300')).toBeInTheDocument();
      expect(screen.getByText('3,200')).toBeInTheDocument();
      expect(screen.getByText('500')).toBeInTheDocument();
    });

    expect(screen.getByText(/START DETECTION →/i)).toBeInTheDocument();
    expect(screen.getByText(/INTELLIGENCE IN THE DARK/i)).toBeInTheDocument();
  });

  it('renders zero metrics and appropriate empty states when no previous detections exist', async () => {
    (api.getStats as any).mockResolvedValue({
      total_records_analyzed: 0,
      predicted_normal_count: 0,
      predicted_malicious_count: 0,
      attack_percentage: 0.0,
      severity_distribution: {
        Normal: 0,
        Low: 0,
        Medium: 0,
        High: 0,
      },
      most_recent_detection_timestamp: null,
    });

    (api.getHistory as any).mockResolvedValue([]);

    render(
      <MemoryRouter>
        <Overview />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('0')).toHaveLength(4);
    });

    expect(screen.getByText(/NO RECENT DETECTION INCIDENTS RECORDED/i)).toBeInTheDocument();
  });
});
