'use client';
import { useEffect } from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="w-14 h-14 rounded-full bg-danger-soft flex items-center justify-center mb-4">
        <ExclamationTriangleIcon className="w-7 h-7 text-danger" aria-hidden="true" />
      </div>
      <h1 className="text-xl font-semibold text-ink">Something went wrong</h1>
      <p className="text-sm text-ink-muted mt-2 max-w-sm">
        An unexpected error occurred. You can try to recover, or return to the dashboard.
      </p>
      {error.digest && (
        <p className="mt-2 text-xs font-mono text-steel">Error ID: {error.digest}</p>
      )}
      <div className="mt-6 flex gap-3">
        <button
          onClick={reset}
          className="px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
        >
          Try again
        </button>
        <a
          href="/dashboard"
          className="px-4 py-2 bg-surface border border-border text-ink rounded text-sm font-medium hover:bg-surface-muted transition-colors"
        >
          Go to Dashboard
        </a>
      </div>
    </div>
  );
}
