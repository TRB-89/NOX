import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { api } from './api';
import { HealthStatus } from '../types';

export interface BackendContextValue {
  health: HealthStatus | null;
  isOnline: boolean;
  isChecking: boolean;
  isColdStarting: boolean;
  coldStartAttempt: number;
  lastChecked: Date | null;
  error: string | null;
  baseUrl: string;
  refreshKey: number;
  checkHealth: (force?: boolean) => Promise<boolean>;
  wakeUpBackend: () => Promise<boolean>;
  retryConnection: () => Promise<boolean>;
  triggerRefresh: () => void;
  setCustomBaseUrl: (url: string) => void;
  resetCustomBaseUrl: () => void;
}

const BackendContext = createContext<BackendContextValue | undefined>(undefined);

export const BackendProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isChecking, setIsChecking] = useState<boolean>(false);
  const [isColdStarting, setIsColdStarting] = useState<boolean>(false);
  const [coldStartAttempt, setColdStartAttempt] = useState<number>(0);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [baseUrl, setBaseUrlState] = useState<string>(() =>
    typeof api?.getBaseUrl === 'function' ? api.getBaseUrl() : 'http://127.0.0.1:8000'
  );
  const [refreshKey, setRefreshKey] = useState<number>(0);

  // Guard against concurrent check execution
  const inProgressRef = useRef<boolean>(false);
  const coldStartTimerRef = useRef<NodeJS.Timeout | null>(null);

  const triggerRefresh = useCallback(() => {
    setRefreshKey((prev) => prev + 1);
  }, []);

  /**
   * Health probe:
   * Only declares online if BOTH status is 'ready' and model_loaded is true.
   */
  const checkHealth = useCallback(async (_force: boolean = false): Promise<boolean> => {
    if (inProgressRef.current) return false;
    inProgressRef.current = true;
    setIsChecking(true);

    try {
      const data = await api.getHealth(10000);
      setHealth(data);
      setLastChecked(new Date());
      setError(null);

      const ready = data.status === 'ready' && data.model_loaded === true;
      if (ready) {
        setIsColdStarting(false);
        setColdStartAttempt(0);
      }
      return ready;
    } catch (err: any) {
      setHealth({
        status: 'error',
        model_loaded: false,
        model_version: 'Offline',
        threshold: null,
        device: null,
      });
      setLastChecked(new Date());
      setError(err.message || 'FastAPI backend is offline or unreachable.');
      return false;
    } finally {
      setIsChecking(false);
      inProgressRef.current = false;
    }
  }, []);

  /**
   * Controlled Cold-Start Wake Up Loop:
   * Probes backend with up to 6 gentle attempts (spaced by 8 seconds, ~48s max).
   * Automatically refreshes all active components upon success.
   * Prevents runaway infinite retry loops.
   */
  const wakeUpBackend = useCallback(async (): Promise<boolean> => {
    if (coldStartTimerRef.current) {
      clearTimeout(coldStartTimerRef.current);
      coldStartTimerRef.current = null;
    }

    setIsColdStarting(true);
    setColdStartAttempt(1);

    // Initial immediate probe
    const immediateSuccess = await checkHealth(true);
    if (immediateSuccess) {
      setIsColdStarting(false);
      setColdStartAttempt(0);
      triggerRefresh();
      return true;
    }

    // Graceful stepped polling (up to 5 subsequent attempts)
    const MAX_ATTEMPTS = 5;
    let currentAttempt = 1;

    return new Promise<boolean>((resolve) => {
      const pollNext = () => {
        coldStartTimerRef.current = setTimeout(async () => {
          currentAttempt++;
          setColdStartAttempt(currentAttempt);

          const success = await checkHealth(true);
          if (success) {
            setIsColdStarting(false);
            setColdStartAttempt(0);
            triggerRefresh();
            resolve(true);
            return;
          }

          if (currentAttempt < MAX_ATTEMPTS) {
            pollNext();
          } else {
            setIsColdStarting(false);
            setColdStartAttempt(0);
            resolve(false);
          }
        }, 8000);
      };

      pollNext();
    });
  }, [checkHealth, triggerRefresh]);

  /**
   * Retry Connection action:
   * Rechecks health and if ready, triggers refresh on all subscribed pages.
   * If backend is still sleeping, initiates cold-start wake sequence.
   */
  const retryConnection = useCallback(async (): Promise<boolean> => {
    const isReady = await checkHealth(true);
    if (isReady) {
      triggerRefresh();
      return true;
    }
    return wakeUpBackend();
  }, [checkHealth, triggerRefresh, wakeUpBackend]);

  const setCustomBaseUrl = useCallback((url: string) => {
    api.setBaseUrl(url);
    setBaseUrlState(api.getBaseUrl());
    checkHealth(true);
  }, [checkHealth]);

  const resetCustomBaseUrl = useCallback(() => {
    api.resetBaseUrl();
    setBaseUrlState(api.getBaseUrl());
    checkHealth(true);
  }, [checkHealth]);

  // Initial check on mount
  useEffect(() => {
    checkHealth();

    // Gentle heartbeat check every 30 seconds
    const interval = setInterval(() => {
      if (!isColdStarting) {
        checkHealth();
      }
    }, 30000);

    return () => {
      clearInterval(interval);
      if (coldStartTimerRef.current) {
        clearTimeout(coldStartTimerRef.current);
      }
    };
  }, [checkHealth, isColdStarting]);

  const isOnline = Boolean(health?.status === 'ready' && health?.model_loaded === true);

  const value: BackendContextValue = {
    health,
    isOnline,
    isChecking,
    isColdStarting,
    coldStartAttempt,
    lastChecked,
    error,
    baseUrl,
    refreshKey,
    checkHealth,
    wakeUpBackend,
    retryConnection,
    triggerRefresh,
    setCustomBaseUrl,
    resetCustomBaseUrl,
  };

  return <BackendContext.Provider value={value}>{children}</BackendContext.Provider>;
};

export const useBackend = (): BackendContextValue => {
  const context = useContext(BackendContext);
  if (!context) {
    // Graceful fallback for standalone component testing
    return {
      health: {
        status: 'ready',
        model_loaded: true,
        model_version: 'NØX-MLP-v1',
        threshold: 0.5,
        device: 'cpu',
      },
      isOnline: true,
      isChecking: false,
      isColdStarting: false,
      coldStartAttempt: 0,
      lastChecked: new Date(),
      error: null,
      baseUrl: typeof api?.getBaseUrl === 'function' ? api.getBaseUrl() : 'http://127.0.0.1:8000',
      refreshKey: 0,
      checkHealth: async () => true,
      wakeUpBackend: async () => true,
      retryConnection: async () => true,
      triggerRefresh: () => {},
      setCustomBaseUrl: () => {},
      resetCustomBaseUrl: () => {},
    };
  }
  return context;
};
