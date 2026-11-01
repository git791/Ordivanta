'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import {
  Squares2X2Icon,
  CalendarDaysIcon,
  UsersIcon,
  CubeIcon,
  ClockIcon,
  BeakerIcon,
  Cog6ToothIcon,
  BellIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: Squares2X2Icon },
  { href: '/schedule', label: 'Planner', icon: CalendarDaysIcon, highlight: true },
  { href: '/workforce', label: 'Workforce', icon: UsersIcon },
  { href: '/units', label: 'Cells', icon: CubeIcon },
  { href: '/shifts', label: 'Shifts', icon: ClockIcon },
  { href: '/experiments', label: 'Experiments', icon: BeakerIcon },
  { href: '/demo', label: 'Demo', icon: SparklesIcon },
  { href: '/settings', label: 'Settings', icon: Cog6ToothIcon },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [plant, setPlant] = useState('Detroit Plant #1');
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="min-h-screen bg-canvas text-ink flex flex-col font-sans antialiased w-full max-w-full overflow-x-hidden">
      {/* ─── Truck&Co Inspired Floating / Pill Top Navigation ─────────────── */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-border/80 shadow-2xs w-full">
        <div className="w-full max-w-7xl 2xl:max-w-[1440px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
          
          {/* Left: Brand Identity with Official Logo */}
          <div className="flex items-center gap-2 shrink-0">
            <Link href="/dashboard" className="flex items-center gap-2.5 group">
              <div className="relative w-8 h-8 flex items-center justify-center shrink-0">
                <Image
                  src="/logo-icon.png"
                  alt="Ordivanta Monogram Logo"
                  width={32}
                  height={32}
                  className="object-contain group-hover:scale-105 transition-transform"
                  priority
                />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-sm sm:text-base tracking-tight text-slate-900 font-sans">Ordivanta</span>
                  <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.2 bg-purple-100 text-purple-800 rounded">
                    PLANT OS
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 -mt-0.5 hidden sm:block">Workforce Scheduling</span>
              </div>
            </Link>
          </div>

          {/* Center: Truck&Co Navigation Pill Container */}
          <nav aria-label="Main Navigation" className="hidden lg:flex items-center bg-slate-100/90 p-1 rounded-full border border-slate-200/80 shadow-2xs shrink">
            {NAV_ITEMS.map(({ href, label, icon: Icon, highlight }) => {
              const active = pathname === href || pathname.startsWith(href + '/');
              return (
                <Link
                  key={href}
                  href={href}
                  className={clsx(
                    'flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all duration-150 whitespace-nowrap',
                    active
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-white/70',
                    highlight && !active && 'text-purple-700 font-semibold'
                  )}
                >
                  <Icon className={clsx('w-3.5 h-3.5 shrink-0', active ? 'text-white' : highlight ? 'text-purple-600' : 'text-slate-500')} />
                  <span>{label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right: Search, Plant Context, Supervisor Role & Action */}
          <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
            {/* Quick Search */}
            <div className="relative hidden 2xl:block">
              {isSearching ? (
                <div className="flex items-center bg-white border border-primary rounded-full px-3 py-1 shadow-xs">
                  <MagnifyingGlassIcon className="w-3.5 h-3.5 text-primary shrink-0 mr-1.5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search worker, cell..."
                    className="text-xs bg-transparent outline-none w-36 text-ink"
                    autoFocus
                    onBlur={() => !searchQuery && setIsSearching(false)}
                  />
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsSearching(true)}
                  className="w-7 h-7 rounded-full bg-slate-100 hover:bg-slate-200 border border-slate-200 flex items-center justify-center text-slate-600 transition-colors"
                  title="Search"
                >
                  <MagnifyingGlassIcon className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Notification Bell */}
            <Link
              href="/dashboard"
              className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-slate-100 hover:bg-slate-200 border border-slate-200 flex items-center justify-center text-slate-600 transition-colors relative shrink-0"
              title="Supervisory Alerts"
            >
              <BellIcon className="w-4 h-4" />
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white" />
            </Link>

            {/* Plant Context & Supervisor Pill */}
            <div className="flex items-center gap-1.5 bg-slate-100/90 border border-slate-200/90 rounded-full px-2.5 py-1 text-xs shrink-0">
              <div className="w-5 h-5 rounded-full bg-purple-600 text-white flex items-center justify-center font-bold text-[9px] shrink-0">
                EV
              </div>
              <div className="hidden xl:flex flex-col text-left">
                <span className="font-semibold text-slate-900 leading-tight text-[11px]">Elena Vance</span>
                <span className="text-[9px] text-slate-500 leading-none">Supervisor</span>
              </div>
              <div className="h-3 w-px bg-slate-300 mx-0.5 hidden xl:block" />
              <div className="flex items-center gap-1 text-slate-700 font-medium text-[11px]">
                <span className="truncate max-w-[95px] hidden sm:inline">{plant}</span>
              </div>
            </div>

            {/* Main Action: New Schedule / Solve */}
            <Link
              href="/schedule"
              className="flex items-center gap-1.5 bg-purple-600 hover:bg-purple-700 text-white px-3 py-1.5 rounded-full text-xs font-semibold shadow-2xs hover:shadow-xs transition-all shrink-0"
            >
              <SparklesIcon className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Optimize</span>
            </Link>
          </div>
        </div>

        {/* Mobile / Tablet Horizontal Sub-Navigation */}
        <div className="lg:hidden flex items-center overflow-x-auto px-4 py-2 border-t border-slate-100 gap-1.5 bg-slate-50/60 no-scrollbar">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href + '/');
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors',
                  active
                    ? 'bg-slate-900 text-white shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900 bg-white border border-slate-200/60'
                )}
              >
                <Icon className={clsx('w-3.5 h-3.5', active ? 'text-white' : 'text-slate-500')} />
                <span>{label}</span>
              </Link>
            );
          })}
        </div>
      </header>

      {/* ─── Main Workspace Container ───────────────────────────────────── */}
      <main className="flex-1 w-full max-w-7xl 2xl:max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>

      {/* ─── Minimal Executive Footer ────────────────────────────────────── */}
      <footer className="border-t border-border/80 bg-white/60 py-4 text-xs text-ink-muted">
        <div className="w-full max-w-7xl 2xl:max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Image
              src="/logo-icon.png"
              alt="Ordivanta Icon"
              width={16}
              height={16}
              className="object-contain"
            />
            <span className="font-semibold text-slate-800">Ordivanta Manufacturing Intelligence</span>
            <span>&bull;</span>
            <span>Detroit Assembly Plant #1</span>
          </div>
          <div className="flex items-center gap-4 text-slate-500">
            <span>HiGHS/PuLP MILP Engine</span>
            <span>&bull;</span>
            <span>Rest Compliance &ge; 11h</span>
            <span>&bull;</span>
            <span className="font-mono">v2.4-prod</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
