import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Detection } from '../pages/Detection';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    uploadCSV: vi.fn(),
  },
}));

describe('Neural Detection Page & CSV Upload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders upload instructions and browse button', () => {
    render(
      <MemoryRouter>
        <Detection />
      </MemoryRouter>
    );

    expect(screen.getByText('NEURAL DETECTION ENGINE')).toBeInTheDocument();
    expect(screen.getByText(/DRAG AND DROP CSV FILE HERE/i)).toBeInTheDocument();
    expect(screen.getByText(/START NEURAL INFERENCE →/i)).toBeInTheDocument();
  });

  it('rejects unsupported non-CSV files', () => {
    const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});

    render(
      <MemoryRouter>
        <Detection />
      </MemoryRouter>
    );

    const input = document.getElementById('csv-file-input') as HTMLInputElement;
    const invalidFile = new File(['binary content'], 'malware_sample.exe', {
      type: 'application/x-msdownload',
    });

    fireEvent.change(input, { target: { files: [invalidFile] } });

    expect(alertMock).toHaveBeenCalledWith(
      'Invalid file format. Please upload a .csv network traffic file.'
    );
    alertMock.mockRestore();
  });

  it('submits valid CSV and displays detection results successfully', async () => {
    (api.uploadCSV as any).mockResolvedValue({
      status: 'success',
      total_records_analyzed: 100,
      normal_traffic_count: 85,
      potential_attack_count: 15,
      attack_percentage: 15.0,
      severity_distribution: {
        Normal: 85,
        Low: 5,
        Medium: 7,
        High: 3,
      },
      preview_limit: 10,
      preview_predictions: [
        {
          prediction: 'Malicious',
          class_id: 1,
          attack_score: 0.954,
          threshold: 0.5,
          severity: 'High',
          model: 'NØX-MLP-v1',
          timestamp: '2026-10-22T21:00:00Z',
        },
        {
          prediction: 'Normal',
          class_id: 0,
          attack_score: 0.042,
          threshold: 0.5,
          severity: 'Normal',
          model: 'NØX-MLP-v1',
          timestamp: '2026-10-22T21:00:00Z',
        },
      ],
    });

    render(
      <MemoryRouter>
        <Detection />
      </MemoryRouter>
    );

    const input = document.getElementById('csv-file-input') as HTMLInputElement;
    const validFile = new File(['proto,service,sbytes\ntcp,http,1024\n'], 'network_flows.csv', {
      type: 'text/csv',
    });

    fireEvent.change(input, { target: { files: [validFile] } });

    expect(screen.getByText('network_flows.csv')).toBeInTheDocument();
    expect(screen.getByText(/READY FOR NEURAL CLASSIFICATION/i)).toBeInTheDocument();

    const submitBtn = screen.getByText(/START NEURAL INFERENCE →/i);
    fireEvent.submit(submitBtn.closest('form')!);

    await waitFor(() => {
      expect(api.uploadCSV).toHaveBeenCalledWith(validFile);
    });

    await waitFor(() => {
      expect(screen.getByText('DETECTION COMPLETE')).toBeInTheDocument();
      expect(screen.getByText('PREDICTED NORMAL')).toBeInTheDocument();
      expect(screen.getByText('POTENTIAL ATTACKS')).toBeInTheDocument();
    });
  });

  it('renders error notification when CSV upload fails', async () => {
    (api.uploadCSV as any).mockRejectedValue(
      new Error('The uploaded CSV does not contain required network flow features.')
    );

    render(
      <MemoryRouter>
        <Detection />
      </MemoryRouter>
    );

    const input = document.getElementById('csv-file-input') as HTMLInputElement;
    const file = new File(['bad_content'], 'corrupt.csv', { type: 'text/csv' });

    fireEvent.change(input, { target: { files: [file] } });

    const submitBtn = screen.getByText(/START NEURAL INFERENCE →/i);
    fireEvent.submit(submitBtn.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText(/ANALYSIS FAILED:/i)).toBeInTheDocument();
      expect(
        screen.getByText(/The uploaded CSV does not contain required network flow features./i)
      ).toBeInTheDocument();
    });
  });
});
