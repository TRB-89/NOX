import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, AlertCircle, X, CheckCircle2 } from 'lucide-react';

interface CSVUploaderProps {
  onUpload: (file: File) => Promise<void>;
  isLoading: boolean;
  error: string | null;
  onClearError: () => void;
}

export const CSVUploader: React.FC<CSVUploaderProps> = ({
  onUpload,
  isLoading,
  error,
  onClearError,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const validateAndSetFile = (file: File) => {
    onClearError();
    if (!file.name.toLowerCase().endsWith('.csv')) {
      alert('Invalid file format. Please upload a .csv network traffic file.');
      return;
    }
    if (file.size === 0) {
      alert('Selected file is empty.');
      return;
    }
    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || isLoading) return;
    await onUpload(selectedFile);
  };

  const handleReset = () => {
    setSelectedFile(null);
    onClearError();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="border-industrial bg-surface p-6">
      <div className="mb-4">
        <h3 className="font-display text-base font-bold tracking-tight text-chrome uppercase">
          NEURAL DETECTION ENGINE
        </h3>
        <p className="font-sans text-xs text-muted mt-1">
          Upload recorded network traffic flow CSV for neural network analysis.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Drag and Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed p-8 text-center cursor-pointer transition-all duration-200 ${
            isDragOver
              ? 'border-accent bg-accent/5'
              : selectedFile
              ? 'border-border-chrome bg-surface-elevated'
              : 'border-border hover:border-chrome bg-background/50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
            id="csv-file-input"
          />

          {selectedFile ? (
            <div className="flex flex-col items-center">
              <FileText className="w-10 h-10 text-chrome mb-3" />
              <span className="font-mono text-sm text-chrome font-semibold break-all">
                {selectedFile.name}
              </span>
              <span className="font-mono text-xs text-muted mt-1">
                Size: {formatFileSize(selectedFile.size)}
              </span>
              <div className="mt-3 flex items-center gap-1.5 text-success font-mono text-xs">
                <CheckCircle2 className="w-4 h-4" />
                <span>READY FOR NEURAL CLASSIFICATION</span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <UploadCloud className="w-10 h-10 text-muted mb-3 group-hover:text-chrome" />
              <span className="font-mono text-xs uppercase tracking-wider text-chrome font-semibold">
                DRAG AND DROP CSV FILE HERE
              </span>
              <span className="font-sans text-xs text-muted mt-1">
                or click to browse your computer
              </span>
              <span className="font-mono text-[10px] text-muted/60 mt-3 border border-border px-2 py-0.5">
                MAX: 50 MB / UNSW-NB15 SCHEMA
              </span>
            </div>
          )}
        </div>

        {/* Error Notification */}
        {error && (
          <div className="mt-4 p-3 border border-accent/60 bg-accent/10 flex items-start gap-2.5 text-xs font-mono text-chrome">
            <AlertCircle className="w-4 h-4 text-accent shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="text-accent font-semibold block uppercase">ANALYSIS FAILED:</span>
              <span>{error}</span>
            </div>
            <button
              type="button"
              onClick={onClearError}
              className="text-muted hover:text-chrome p-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Controls */}
        <div className="mt-5 flex items-center justify-between gap-4">
          <button
            type="button"
            onClick={handleReset}
            disabled={!selectedFile || isLoading}
            className="px-4 py-2 border border-border text-xs font-mono uppercase tracking-wider text-muted hover:text-chrome hover:border-chrome disabled:opacity-40 transition-colors"
          >
            RESET
          </button>

          <button
            type="submit"
            disabled={!selectedFile || isLoading}
            className="flex-1 sm:flex-initial px-6 py-2.5 bg-accent hover:bg-accent-hover text-white text-xs font-mono uppercase tracking-wider font-semibold transition-colors disabled:opacity-40 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>ANALYZING NETWORK RECORDS...</span>
              </>
            ) : (
              <span>START NEURAL INFERENCE →</span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
