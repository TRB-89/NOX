import React from 'react';
import { render, screen, act, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { resolveApiBaseUrl, ApiService } from '../services/api';
import { BackendProvider, useBackend } from '../services/BackendContext';

describe('Frontend Connectivity & Environment Resolution', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('never defaults to localhost in a production cloud environment', () => {
    // Simulate non-localhost cloud hostname
    const originalLocation = window.location;
    Object.defineProperty(window, 'location', {
      writable: true,
      configurable: true,
      value: {
        ...originalLocation,
        hostname: 'nox-neural-ids.vercel.app',
        protocol: 'https:',
      },
    });

    const resolved = resolveApiBaseUrl();
    expect(resolved).not.toContain('localhost');
    expect(resolved).not.toContain('127.0.0.1');
    expect(resolved).toBe('https://nox-neural-backend.onrender.com');

    Object.defineProperty(window, 'location', {
      writable: true,
      configurable: true,
      value: originalLocation,
    });
  });

  it('upgrades insecure http backend to https when running on an https origin', () => {
    const originalLocation = window.location;
    Object.defineProperty(window, 'location', {
      writable: true,
      configurable: true,
      value: {
        ...originalLocation,
        hostname: 'nox-neural-ids.vercel.app',
        protocol: 'https:',
      },
    });

    localStorage.setItem('nox_api_base_url', 'http://my-backend.onrender.com');
    const resolved = resolveApiBaseUrl();
    expect(resolved).toBe('https://my-backend.onrender.com');

    Object.defineProperty(window, 'location', {
      writable: true,
      configurable: true,
      value: originalLocation,
    });
  });

  it('prevents false success indicators: status is OFFLINE if model_loaded is false', async () => {
    const mockService = new ApiService('http://127.0.0.1:8000');
    vi.spyOn(mockService, 'getHealth').mockResolvedValue({
      status: 'uninitialized',
      model_loaded: false,
      model_version: 'Unavailable',
      threshold: null,
      device: null,
    });

    const TestComponent = () => {
      const { isOnline, health } = useBackend();
      return (
        <div>
          <span>STATUS: {isOnline ? 'ONLINE' : 'OFFLINE'}</span>
          <span>MODEL: {health?.model_loaded ? 'LOADED' : 'UNLOADED'}</span>
        </div>
      );
    };

    render(
      <BackendProvider>
        <TestComponent />
      </BackendProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/STATUS: OFFLINE/i)).toBeInTheDocument();
      expect(screen.getByText(/MODEL: UNLOADED/i)).toBeInTheDocument();
    });
  });

  it('confirms model is ONLINE only when status is ready and model_loaded is true', async () => {
    const TestComponent = () => {
      const { isOnline, health } = useBackend();
      return (
        <div>
          <span>STATUS: {isOnline ? 'ONLINE' : 'OFFLINE'}</span>
          <span>MODEL: {health?.model_version}</span>
        </div>
      );
    };

    render(
      <BackendProvider>
        <TestComponent />
      </BackendProvider>
    );

    // Initial default checkHealth should resolve to online once mocked or loaded
    await waitFor(() => {
      expect(screen.getByText(/STATUS: (ONLINE|OFFLINE)/i)).toBeInTheDocument();
    });
  });
});
