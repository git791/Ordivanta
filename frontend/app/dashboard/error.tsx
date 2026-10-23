'use client';
import { useEffect } from 'react';
import ErrorBanner from '@/components/ui/ErrorBanner';

export default function DashboardError({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-ink">Dashboard</h1>
      <ErrorBanner
        title="Failed to load dashboard"
        message={error.message || 'Unable to reach the backend API. Check that the server is running.'}
      />
      <button
        onClick={reset}
        className="px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors"
      >
        Retry
      </button>
    </div>
  );
}
