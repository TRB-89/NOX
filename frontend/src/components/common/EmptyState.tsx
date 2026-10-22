import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Database } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  message?: string;
  actionText?: string;
  actionLabel?: string;
  actionPath?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'NO DETECTION EVENTS RECORDED',
  description,
  message,
  actionText,
  actionLabel,
  actionPath,
  onAction,
}) => {
  const navigate = useNavigate();
  const desc =
    description ||
    message ||
    'No network traffic flow records have been processed yet. Upload a dataset to begin inference.';
  const btnText = actionText || actionLabel;

  const handleClick = () => {
    if (onAction) {
      onAction();
    } else if (actionPath) {
      navigate(actionPath);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-12 text-center border-industrial bg-surface my-6">
      <div className="p-3 border border-border mb-4 bg-background">
        <Database className="w-8 h-8 text-muted" />
      </div>
      <h3 className="font-mono text-sm tracking-widest text-chrome uppercase font-semibold">
        {title}
      </h3>
      <p className="font-sans text-xs text-muted max-w-md mt-2 leading-relaxed">
        {desc}
      </p>
      {btnText && (
        <button
          onClick={handleClick}
          className="mt-6 px-4 py-2 border border-border hover:border-chrome text-xs font-mono text-chrome uppercase tracking-wider transition-colors duration-200"
        >
          {btnText}
        </button>
      )}
    </div>
  );
};
