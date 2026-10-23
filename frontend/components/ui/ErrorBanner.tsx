import React from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface ErrorBannerProps {
  title?: string;
  message?: string;
  errors?: string[];
  className?: string;
}

export default function ErrorBanner({ title = 'An error occurred', message, errors, className }: ErrorBannerProps) {
  return (
    <div
      role="alert"
      className={`bg-danger-soft border border-danger rounded-lg p-4 ${className ?? ''}`}
    >
      <div className="flex items-start gap-3">
        <ExclamationTriangleIcon className="w-5 h-5 text-danger shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <p className="text-sm font-semibold text-danger">{title}</p>
          {message && <p className="text-sm text-danger mt-1">{message}</p>}
          {errors && errors.length > 0 && (
            <ul className="mt-2 space-y-1 list-disc list-inside text-sm text-danger">
              {errors.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
