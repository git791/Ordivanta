'use client';
import { useEffect } from 'react';
import ErrorBanner from '@/components/ui/ErrorBanner';
import Link from 'next/link';

export default function ScheduleError({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-ink">Schedule</h1>
      <ErrorBanner
        title="Schedule operation failed"
        message={error.message}
      />
      <div className="flex gap-3">
        <button
          onClick={reset}
          className="px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors"
        >
          Retry
        </button>
        <Link href="/dashboard" className="px-4 py-2 border border-border rounded text-sm text-ink hover:bg-surface-muted">
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
