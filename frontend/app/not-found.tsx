import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <p className="text-5xl font-mono font-semibold text-border mb-4" aria-hidden="true">404</p>
      <h1 className="text-xl font-semibold text-ink">Page not found</h1>
      <p className="text-sm text-ink-muted mt-2 max-w-sm">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link
        href="/dashboard"
        className="mt-6 inline-flex items-center gap-2 px-4 py-2 bg-primary text-white rounded text-sm font-medium hover:bg-primary-hover transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
      >
        Return to Dashboard
      </Link>
    </div>
  );
}
