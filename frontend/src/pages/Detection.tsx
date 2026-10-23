import React, { useState } from 'react';
import { CSVUploader } from '../components/detection/CSVUploader';
import { DetectionResults } from '../components/detection/DetectionResults';
import { PredictionTable } from '../components/detection/PredictionTable';
import { api } from '../services/api';
import { CSVUploadResponse } from '../types';
import { Shield, Cpu, AlertCircle, FileCheck, Layers } from 'lucide-react';

import { useBackend } from '../services/BackendContext';

export const Detection: React.FC = () => {
  const { triggerRefresh } = useBackend();
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadResults, setUploadResults] = useState<CSVUploadResponse | null>(null);

  const handleUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.uploadCSV(file);
      setUploadResults(response);
      triggerRefresh();
    } catch (err: any) {
      setError(err.message || 'CSV upload and inference analysis failed.');
      setUploadResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearError = () => {
    setError(null);
  };

  const handleReset = () => {
    setUploadResults(null);
    setError(null);
  };

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Page Header */}
      <div className="border-b border-border pb-6">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-mono text-xs uppercase tracking-widest text-accent font-semibold">
            02 // INFERENCE ENGINE
          </span>
          <span className="text-muted font-mono text-xs">•</span>
          <span className="font-mono text-xs text-muted">BATCH CSV UPLOAD</span>
        </div>
        <h1 className="font-display text-3xl font-extrabold uppercase tracking-tight text-chrome">
          NEURAL DETECTION
        </h1>
        <p className="font-sans text-sm text-muted mt-2 max-w-2xl">
          Feed recorded network traffic flows into the PyTorch Multilayer Perceptron detection pipeline.
          Data is preprocessed via the trained scikit-learn standardizer and evaluated against probability thresholds.
        </p>
      </div>

      {/* CSV Upload Section */}
      <section>
        <CSVUploader
          onUpload={handleUpload}
          isLoading={isLoading}
          error={error}
          onClearError={handleClearError}
        />
      </section>

      {/* Results Section */}
      {uploadResults && (
        <section className="space-y-8 animate-fade-in">
          {/* Summary and Metrics */}
          <DetectionResults results={uploadResults} onReset={handleReset} />

          {/* Detailed Preview Prediction Table */}
          {uploadResults.preview_predictions && uploadResults.preview_predictions.length > 0 && (
            <PredictionTable
              predictions={uploadResults.preview_predictions}
              title={`PREVIEW PREDICTIONS (${uploadResults.preview_predictions.length} SAMPLES)`}
            />
          )}
        </section>
      )}

      {/* Technical Specifications Callout */}
      <section className="border-industrial bg-surface p-6">
        <h3 className="font-display text-xs font-bold uppercase tracking-widest text-muted mb-4">
          TECHNICAL PIPELINE SPECIFICATIONS
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
          <div className="p-4 bg-surface-elevated border border-border">
            <div className="flex items-center gap-2 text-chrome mb-2">
              <Cpu className="w-4 h-4 text-accent" />
              <span className="font-bold">INFERENCE MODEL</span>
            </div>
            <p className="font-sans text-muted text-xs leading-relaxed">
              PyTorch MLP (3-layer architecture: 43 → 128 → 64 → 1) with BatchNorm, Dropout(0.3), and Sigmoid activation.
            </p>
          </div>

          <div className="p-4 bg-surface-elevated border border-border">
            <div className="flex items-center gap-2 text-chrome mb-2">
              <Layers className="w-4 h-4 text-chrome" />
              <span className="font-bold">PREPROCESSING</span>
            </div>
            <p className="font-sans text-muted text-xs leading-relaxed">
              One-Hot Encoding for categorical features (`proto`, `service`, `state`) and Robust/Standard scaling for numerical features.
            </p>
          </div>

          <div className="p-4 bg-surface-elevated border border-border">
            <div className="flex items-center gap-2 text-chrome mb-2">
              <FileCheck className="w-4 h-4 text-success" />
              <span className="font-bold">AUDIT PERSISTENCE</span>
            </div>
            <p className="font-sans text-muted text-xs leading-relaxed">
              All parsed records and output classification scores are automatically written to SQLite audit storage.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
