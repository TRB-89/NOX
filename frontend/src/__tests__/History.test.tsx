import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { History } from '../pages/History';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    getHistory: vi.fn(),
  },
}));

describe('Detection History Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockEvents = [
    {
      id: 101,
      timestamp: '2026-10-22T21:15:00Z',
      prediction: 'Malicious',
      class_id: 1,
      attack_score: 0.985,
      threshold: 0.5,
      severity: 'High',
      model_version: 'NØX-MLP-v1',
      source_type: 'csv_upload',
    },
    {
      id: 102,
      timestamp: '2026-10-22T21:16:00Z',
      prediction: 'Normal',
      class_id: 0,
      attack_score: 0.05,
      threshold: 0.5,
      severity: 'Normal',
      model_version: 'NØX-MLP-v1',
      source_type: 'single',
    },
  ];

  it('renders history table rows with real timestamps and scores', async () => {
    (api.getHistory as any).mockResolvedValue(mockEvents);

    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('#00101')).toBeInTheDocument();
      expect(screen.getByText('#00102')).toBeInTheDocument();
    });

    expect(screen.getAllByText(/MALICIOUS/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/NORMAL/i).length).toBeGreaterThan(0);
    expect(screen.getByText('98.5%')).toBeInTheDocument();
  });

  it('opens detailed inspection modal when an event is clicked', async () => {
    (api.getHistory as any).mockResolvedValue(mockEvents);

    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('#00101')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('#00101'));

    expect(screen.getByText('AUDIT EVENT DETAIL #101')).toBeInTheDocument();
    expect(screen.getByText(/DECISION THRESHOLD:/i)).toBeInTheDocument();
    expect(screen.getByText('NØX-MLP-v1')).toBeInTheDocument();
  });

  it('shows empty state when no historical events exist', async () => {
    (api.getHistory as any).mockResolvedValue([]);

    render(
      <MemoryRouter>
        <History />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/NO AUDIT RECORDS FOUND/i)).toBeInTheDocument();
    });
  });
});
