'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  BellIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  BoltIcon,
  InformationCircleIcon,
  XMarkIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import {
  AppNotification,
  getNotifications,
  markAllNotificationsRead,
  dismissNotification,
  subscribeNotifications,
} from '@/lib/notifications';

export default function NotificationDropdown() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initial fetch
    setNotifications(getNotifications());

    // Subscribe to live updates across pages
    const unsubscribe = subscribeNotifications((updated) => {
      setNotifications(updated);
    });

    return () => unsubscribe();
  }, []);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const getSeverityIcon = (severity: AppNotification['severity']) => {
    switch (severity) {
      case 'danger':
        return <ExclamationCircleIcon className="w-4 h-4 text-rose-600 shrink-0" />;
      case 'warning':
        return <ExclamationTriangleIcon className="w-4 h-4 text-amber-600 shrink-0" />;
      case 'success':
        return <CheckCircleIcon className="w-4 h-4 text-emerald-600 shrink-0" />;
      case 'info':
      default:
        return <InformationCircleIcon className="w-4 h-4 text-purple-600 shrink-0" />;
    }
  };

  const getSeverityBadge = (severity: AppNotification['severity']) => {
    switch (severity) {
      case 'danger':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'warning':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'success':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'info':
      default:
        return 'bg-purple-50 text-purple-800 border-purple-200';
    }
  };

  return (
    <div className="relative shrink-0" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className={clsx(
          'w-7 h-7 sm:w-8 sm:h-8 rounded-full border flex items-center justify-center transition-colors relative',
          isOpen
            ? 'bg-slate-900 text-white border-slate-900 shadow-xs'
            : 'bg-slate-100 hover:bg-slate-200 border-slate-200 text-slate-700'
        )}
        title={unreadCount > 0 ? `${unreadCount} unread shop-floor alerts` : 'Supervisory Alerts & Telemetry'}
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-label="Shop-Floor Alerts"
      >
        <BellIcon className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-rose-600 text-white text-[10px] font-bold flex items-center justify-center ring-2 ring-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Floating Tray Dropdown */}
      {isOpen && (
        <div
          role="dialog"
          aria-label="Notifications Tray"
          className="absolute right-0 top-full mt-2 w-80 sm:w-96 bg-white border border-slate-200 rounded-2xl shadow-2xl z-[100] overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150"
        >
          {/* Header */}
          <div className="p-3.5 border-b border-slate-100 bg-slate-50/80 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold text-xs text-slate-900 font-sans">Shop-Floor Alerts</span>
              {unreadCount > 0 ? (
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-rose-100 text-rose-800 border border-rose-200">
                  {unreadCount} new
                </span>
              ) : (
                <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-slate-200 text-slate-600">
                  All clear
                </span>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                type="button"
                onClick={() => markAllNotificationsRead()}
                className="text-[11px] font-medium text-purple-700 hover:text-purple-900 flex items-center gap-1 hover:underline cursor-pointer"
              >
                <CheckIcon className="w-3 h-3" />
                <span>Mark all read</span>
              </button>
            )}
          </div>

          {/* Notifications List */}
          <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
            {notifications.length === 0 ? (
              <div className="p-6 text-center text-slate-400 text-xs">
                <BellIcon className="w-6 h-6 mx-auto mb-1.5 opacity-40" />
                <span>No active alerts. Factory operations running smoothly.</span>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={clsx(
                    'p-3.5 transition-colors relative group hover:bg-slate-50/90',
                    !n.read ? 'bg-purple-50/30' : 'bg-white'
                  )}
                >
                  <div className="flex items-start gap-2.5">
                    <div className="mt-0.5">{getSeverityIcon(n.severity)}</div>

                    <div className="flex-1 min-w-0 pr-4">
                      <div className="flex items-center justify-between gap-1 mb-0.5">
                        <span className="font-semibold text-xs text-slate-900 truncate">{n.title}</span>
                        <span className="text-[10px] font-mono text-slate-400 shrink-0">{n.timestamp}</span>
                      </div>

                      <p className="text-[11px] text-slate-600 leading-snug">{n.message}</p>

                      {n.actionUrl && (
                        <div className="mt-2">
                          <Link
                            href={n.actionUrl}
                            onClick={() => {
                              setIsOpen(false);
                            }}
                            className={clsx(
                              'inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded border transition-colors',
                              getSeverityBadge(n.severity)
                            )}
                          >
                            <span>{n.actionLabel || 'Inspect'}</span>
                            <span aria-hidden="true">&rarr;</span>
                          </Link>
                        </div>
                      )}
                    </div>

                    {/* Dismiss Button */}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        dismissNotification(n.id);
                      }}
                      className="absolute top-3 right-3 text-slate-400 hover:text-slate-700 opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded hover:bg-slate-200/60"
                      title="Dismiss alert"
                    >
                      <XMarkIcon className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="p-2.5 bg-slate-50 border-t border-slate-100 text-center">
            <Link
              href="/dashboard"
              onClick={() => setIsOpen(false)}
              className="text-xs font-semibold text-slate-700 hover:text-slate-900 inline-flex items-center gap-1"
            >
              <span>View Operations Command Center</span>
              <span aria-hidden="true">&rarr;</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
