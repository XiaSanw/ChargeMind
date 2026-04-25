import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { StationProfile, DiagnoseResponse, PageType } from '@/types/diagnosis';

interface DiagnosisState {
  profile: StationProfile | null;
  diagnoseResult: DiagnoseResponse | null;
  currentPage: PageType;
  isDiagnosing: boolean;
  error: string | null;
  landingInput: string | null;
  autoOpenDialog: boolean;
}

interface DiagnosisActions {
  setProfile: (profile: StationProfile) => void;
  updateProfileField: (key: string, value: unknown) => void;
  setDiagnoseResult: (result: DiagnoseResponse) => void;
  setCurrentPage: (page: PageType) => void;
  setIsDiagnosing: (v: boolean) => void;
  setError: (err: string | null) => void;
  reset: () => void;
  setLandingInput: (v: string | null) => void;
  clearAutoOpenDialog: () => void;
}

const DiagnosisContext = createContext<(DiagnosisState & DiagnosisActions) | null>(null);

const STORAGE_KEY = 'chargemind_profile';

export function DiagnosisProvider({ children }: { children: ReactNode }) {
  const [profile, setProfileState] = useState<StationProfile | null>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const [diagnoseResult, setDiagnoseResult] = useState<DiagnoseResponse | null>(null);
  const [currentPage, setCurrentPage] = useState<PageType>('landing');
  const [isDiagnosing, setIsDiagnosing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [landingInput, setLandingInputState] = useState<string | null>(null);
  const [autoOpenDialog, setAutoOpenDialog] = useState(false);

  const setProfile = useCallback((p: StationProfile) => {
    setProfileState(p);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
  }, []);

  const updateProfileField = useCallback((key: string, value: unknown) => {
    setProfileState((prev) => {
      const next = prev ? { ...prev, [key]: value } : { [key]: value };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  const setDiagnoseResultWrapped = useCallback((result: DiagnoseResponse) => {
    setDiagnoseResult(result);
    setIsDiagnosing(false);
  }, []);

  const setErrorWrapped = useCallback((err: string | null) => {
    setError(err);
    setIsDiagnosing(false);
  }, []);

  const reset = useCallback(() => {
    setProfileState(null);
    setDiagnoseResult(null);
    setCurrentPage('landing');
    setIsDiagnosing(false);
    setError(null);
    setLandingInputState(null);
    setAutoOpenDialog(true);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  const setLandingInput = useCallback((v: string | null) => {
    setLandingInputState(v);
  }, []);

  const clearAutoOpenDialog = useCallback(() => {
    setAutoOpenDialog(false);
  }, []);

  return (
    <DiagnosisContext.Provider
      value={{
        profile,
        diagnoseResult,
        currentPage,
        isDiagnosing,
        error,
        landingInput,
        autoOpenDialog,
        setProfile,
        updateProfileField,
        setDiagnoseResult: setDiagnoseResultWrapped,
        setCurrentPage,
        setIsDiagnosing,
        setError: setErrorWrapped,
        reset,
        setLandingInput,
        clearAutoOpenDialog,
      }}
    >
      {children}
    </DiagnosisContext.Provider>
  );
}

export function useDiagnosis() {
  const ctx = useContext(DiagnosisContext);
  if (!ctx) throw new Error('useDiagnosis must be used within DiagnosisProvider');
  return ctx;
}
