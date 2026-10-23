'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import {
  HomeIcon, UsersIcon, CubeIcon, ClockIcon,
  CalendarDaysIcon, BeakerIcon, Cog6ToothIcon
} from '@heroicons/react/24/outline';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: HomeIcon },
  { href: '/workforce', label: 'Workforce', icon: UsersIcon },
  { href: '/units', label: 'Production Units', icon: CubeIcon },
  { href: '/shifts', label: 'Shift Demand', icon: ClockIcon },
  { href: '/schedule', label: 'Schedule Runs', icon: CalendarDaysIcon },
  { href: '/experiments', label: 'Experiments', icon: BeakerIcon },
  { href: '/settings', label: 'Settings', icon: Cog6ToothIcon },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <nav
      aria-label="Main navigation"
      style={{ width: '240px', flexShrink: 0, backgroundColor: 'var(--surface)', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', minHeight: '100vh' }}
    >
      <div style={{ padding: '20px', borderBottom: '1px solid var(--border)' }}>
        <span style={{ fontSize: '18px', fontWeight: 600, color: 'var(--ink)', letterSpacing: '-0.02em' }}>Ordivanta</span>
        <p style={{ fontSize: '12px', color: 'var(--ink-muted)', marginTop: '2px' }}>Workforce Scheduling</p>
      </div>
      <ul style={{ display: 'flex', flexDirection: 'column', gap: '2px', padding: '12px', flex: 1, listStyle: 'none', margin: 0 }}>
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + '/');
          return (
            <li key={href}>
              <Link
                href={href}
                aria-current={active ? 'page' : undefined}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: active ? '8px 12px 8px 10px' : '8px 12px',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: 500,
                  textDecoration: 'none',
                  borderLeft: active ? '2px solid var(--primary)' : '2px solid transparent',
                  backgroundColor: active ? 'var(--primary-soft)' : 'transparent',
                  color: active ? 'var(--primary)' : 'var(--ink-muted)',
                  transition: 'background-color 0.12s, color 0.12s',
                }}
                onMouseEnter={e => {
                  if (!active) {
                    (e.currentTarget as HTMLAnchorElement).style.backgroundColor = 'var(--surface-muted)';
                    (e.currentTarget as HTMLAnchorElement).style.color = 'var(--ink)';
                  }
                }}
                onMouseLeave={e => {
                  if (!active) {
                    (e.currentTarget as HTMLAnchorElement).style.backgroundColor = 'transparent';
                    (e.currentTarget as HTMLAnchorElement).style.color = 'var(--ink-muted)';
                  }
                }}
              >
                <Icon aria-hidden="true" style={{ width: '16px', height: '16px', flexShrink: 0 }} />
                {label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
