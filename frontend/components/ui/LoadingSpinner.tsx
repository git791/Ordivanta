import React from 'react';

export default function LoadingSpinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-12" role="status" aria-label={label}>
      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </div>
  );
}
