import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from '../components/layout/Sidebar';
import { Header } from '../components/layout/Header';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    getHealth: vi.fn(),
  },
}));

describe('Navigation & Layout Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.getHealth as any).mockResolvedValue({
      status: 'ready',
      model_loaded: true,
      model_version: 'NØX-MLP-v1',
      threshold: 0.5,
      device: 'cpu',
    });
  });

  it('renders sidebar navigation links correctly', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Sidebar isOpen={true} onClose={() => {}} />
      </MemoryRouter>
    );

    expect(screen.getByText('NØX')).toBeInTheDocument();
    expect(screen.getByText(/NEURAL INTRUSION SYSTEM/i)).toBeInTheDocument();
    expect(screen.getByText(/Overview/i)).toBeInTheDocument();
    expect(screen.getByText(/Neural Detection/i)).toBeInTheDocument();
    expect(screen.getByText(/Threat Analytics/i)).toBeInTheDocument();
    expect(screen.getByText(/Detection History/i)).toBeInTheDocument();
    expect(screen.getByText(/System Information/i)).toBeInTheDocument();
  });

  it('renders header with current title and connection status', async () => {
    render(
      <Header
        title="Mission Overview"
        subtitle="Live Neural Intrusion Telemetry & System Status"
        onOpenMobileNav={() => {}}
      />
    );

    expect(screen.getByText('Mission Overview')).toBeInTheDocument();
    expect(screen.getByText('Live Neural Intrusion Telemetry & System Status')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/ONLINE/i)).toBeInTheDocument();
    });
  });

  it('triggers mobile navigation callback on hamburger click', () => {
    const handleOpenNav = vi.fn();
    render(
      <Header
        title="Mission Overview"
        subtitle="Test subtitle"
        onOpenMobileNav={handleOpenNav}
      />
    );

    const menuButton = screen.getByLabelText(/Open mobile navigation/i);
    fireEvent.click(menuButton);
    expect(handleOpenNav).toHaveBeenCalledTimes(1);
  });
});
