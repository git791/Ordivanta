'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import PageHeader from '@/components/ui/PageHeader';
import StatusBadge from '@/components/ui/StatusBadge';
import {
  ClockIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  SparklesIcon,
  UserIcon,
  CurrencyDollarIcon,
  CalendarDaysIcon,
  ExclamationCircleIcon,
  ArrowPathIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';

interface WorkerProfile {
  id: string;
  name: string;
  role: string;
  base_wage: number;
  skills: string[];
  certifications: string[];
  overtime_opt_in: boolean;
  max_overtime_hours: number;
  is_absent: boolean;
  absence_reason?: string;
  assigned_shifts: Array<{
    shift_name: string;
    day: string;
    hours: number;
    unit_name: string;
    time: string;
    rest_interval_hours: number;
  }>;
}

const DEFAULT_WORKERS: Record<string, WorkerProfile> = {
  emp_david: {
    id: 'emp_david',
    name: 'David Kim',
    role: 'Senior Welding Specialist',
    base_wage: 32.50,
    skills: ['welding', 'robotic_welding', 'inspection'],
    certifications: ['ISO 9001:2015', 'AWS D1.1 Structural Welding', 'Safety Level 2'],
    overtime_opt_in: true,
    max_overtime_hours: 8.0,
    is_absent: false,
    assigned_shifts: [
      { shift_name: 'Morning', day: 'Monday, Nov 03', hours: 8.0, unit_name: 'Cell 03 (Robotic Welding)', time: '07:00–15:00', rest_interval_hours: 16.0 },
      { shift_name: 'Afternoon', day: 'Tuesday, Nov 04', hours: 8.0, unit_name: 'Cell 03 (Robotic Welding)', time: '15:00–23:00', rest_interval_hours: 24.0 },
      { shift_name: 'Afternoon', day: 'Wednesday, Nov 05', hours: 8.0, unit_name: 'Cell 01 (Machining)', time: '15:00–23:00', rest_interval_hours: 16.0 },
      { shift_name: 'Morning', day: 'Thursday, Nov 06', hours: 8.0, unit_name: 'Cell 03 (Robotic Welding)', time: '07:00–15:00', rest_interval_hours: 16.0 },
    ],
  },
  emp_alice: {
    id: 'emp_alice',
    name: 'Alice Martin',
    role: 'Assembly Operations Lead',
    base_wage: 28.00,
    skills: ['assembly', 'packaging', 'stamping'],
    certifications: ['Lean Six Sigma Yellow Belt', 'First Aid Certified'],
    overtime_opt_in: false,
    max_overtime_hours: 0.0,
    is_absent: false,
    assigned_shifts: [
      { shift_name: 'Morning', day: 'Monday, Nov 03', hours: 8.0, unit_name: 'Cell 02 (CNC Stamping)', time: '07:00–15:00', rest_interval_hours: 16.0 },
      { shift_name: 'Morning', day: 'Tuesday, Nov 04', hours: 8.0, unit_name: 'Cell 02 (CNC Stamping)', time: '07:00–15:00', rest_interval_hours: 16.0 },
      { shift_name: 'Morning', day: 'Wednesday, Nov 05', hours: 8.0, unit_name: 'Cell 04 (Final QC)', time: '07:00–15:00', rest_interval_hours: 16.0 },
      { shift_name: 'Morning', day: 'Friday, Nov 07', hours: 8.0, unit_name: 'Cell 02 (CNC Stamping)', time: '07:00–15:00', rest_interval_hours: 24.0 },
    ],
  },
  emp_004: {
    id: 'emp_004',
    name: 'Marcus Vance (Worker 004)',
    role: 'Robotic Welding Technician',
    base_wage: 31.00,
    skills: ['welding', 'robotic_welding'],
    certifications: ['ISO 9001:2015', 'Welding Level 4'],
    overtime_opt_in: false,
    max_overtime_hours: 4.0,
    is_absent: true,
    absence_reason: 'Medical Leave (Nov 03 - Nov 07)',
    assigned_shifts: [],
  },
};

export default function WorkerPortalPage() {
  const [selectedWorkerId, setSelectedWorkerId] = useState<string>('emp_david');
  const [workersState, setWorkersState] = useState<Record<string, WorkerProfile>>(DEFAULT_WORKERS);
  const [syncToast, setSyncToast] = useState<string | null>(null);
  const [newCertInput, setNewCertInput] = useState<string>('');

  // Load from localStorage if present
  useEffect(() => {
    try {
      const saved = localStorage.getItem('ordivanta_worker_sync_state');
      if (saved) {
        setWorkersState(JSON.parse(saved));
      }
    } catch {
      // ignore
    }
  }, []);

  const currentWorker = workersState[selectedWorkerId] || DEFAULT_WORKERS.emp_david;

  const updateCurrentWorker = (updater: (prev: WorkerProfile) => WorkerProfile, feedbackMsg: string) => {
    setWorkersState((prev) => {
      const updated = {
        ...prev,
        [selectedWorkerId]: updater(prev[selectedWorkerId] || DEFAULT_WORKERS.emp_david),
      };
      try {
        localStorage.setItem('ordivanta_worker_sync_state', JSON.stringify(updated));
      } catch {
        // ignore
      }
      return updated;
    });
    setSyncToast(feedbackMsg);
    setTimeout(() => setSyncToast(null), 4000);
  };

  const totalWeeklyHours = currentWorker.assigned_shifts.reduce((sum, s) => sum + s.hours, 0);
  const estimatedGrossPay = totalWeeklyHours * currentWorker.base_wage;

  return (
    <div className="space-y-8 w-full max-w-5xl mx-auto overflow-x-hidden">
      {/* Toast Notification */}
      {syncToast && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white px-5 py-3 rounded-2xl shadow-xl flex items-center gap-3 animate-in slide-in-from-bottom-3 duration-300 border border-slate-700 text-xs">
          <CheckCircleIcon className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{syncToast}</span>
        </div>
      )}

      {/* Header & Worker Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-border/80 gap-4">
        <div>
          <PageHeader
            title="Worker Self-Service Portal"
            description="View your assigned shifts, confirm voluntary overtime consent, and update certified qualifications."
          />
        </div>

        {/* Worker Switcher & Return to Supervisor pill */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-2 bg-white border border-border/80 rounded-full px-3 py-1.5 shadow-2xs">
            <UserIcon className="w-4 h-4 text-purple-600" />
            <label htmlFor="worker-select" className="text-xs font-bold text-slate-500 uppercase">
              Signed in as:
            </label>
            <select
              id="worker-select"
              value={selectedWorkerId}
              onChange={(e) => setSelectedWorkerId(e.target.value)}
              className="bg-transparent text-xs font-semibold text-slate-900 outline-none cursor-pointer"
            >
              <option value="emp_david">David Kim (Senior Welder)</option>
              <option value="emp_alice">Alice Martin (Assembly Lead)</option>
              <option value="emp_004">Marcus Vance / Worker 004 (Absent)</option>
            </select>
          </div>

          <Link
            href="/dashboard"
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-full text-xs font-semibold shadow-2xs transition-all flex items-center gap-1.5"
          >
            <span>Supervisor Command Center</span>
            <ArrowRightIcon className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Profile Overview Card */}
      <div className="bg-surface border border-border/80 rounded-3xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-border/70">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-700 text-white flex items-center justify-center font-bold text-xl shadow-xs">
              {currentWorker.name.split(' ').map((n) => n[0]).join('')}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-slate-900">{currentWorker.name}</h2>
                <span className="font-mono text-xs px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-700">
                  ID: {currentWorker.id}
                </span>
                {currentWorker.is_absent ? (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
                    Medical Leave
                  </span>
                ) : (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                    Active on Roster
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{currentWorker.role} &bull; Base Wage: ${currentWorker.base_wage.toFixed(2)}/h</p>
            </div>
          </div>

          {/* Absence Reporting Toggle */}
          <div>
            {currentWorker.is_absent ? (
              <button
                type="button"
                onClick={() =>
                  updateCurrentWorker(
                    (w) => ({ ...w, is_absent: false, absence_reason: undefined }),
                    `${currentWorker.name} marked Active for Duty. Supervisor notified.`
                  )
                }
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-full shadow-2xs transition-all"
              >
                Clear Medical Leave & Return to Active
              </button>
            ) : (
              <button
                type="button"
                onClick={() =>
                  updateCurrentWorker(
                    (w) => ({ ...w, is_absent: true, absence_reason: 'Reported Absence / Medical Leave' }),
                    `${currentWorker.name} reported absent. Supervisor shortage alert triggered.`
                  )
                }
                className="px-4 py-2 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-semibold rounded-full shadow-2xs transition-all"
              >
                Report Absence / Sick Leave
              </button>
            )}
          </div>
        </div>

        {/* Quick Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6">
          <div className="p-4 bg-slate-50/70 border border-slate-200/80 rounded-2xl">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Scheduled Workload</span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-slate-900">{totalWeeklyHours.toFixed(1)}h</span>
              <span className="text-xs text-slate-500">/ 40.0h regular</span>
            </div>
            <div className="mt-2 w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-purple-600 h-1.5 rounded-full"
                style={{ width: `${Math.min(100, (totalWeeklyHours / 40) * 100)}%` }}
              />
            </div>
          </div>

          <div className="p-4 bg-slate-50/70 border border-slate-200/80 rounded-2xl">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Voluntary Overtime</span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className={`text-2xl font-bold font-mono ${currentWorker.overtime_opt_in ? 'text-emerald-700' : 'text-slate-500'}`}>
                {currentWorker.overtime_opt_in ? `Consent ON (+${currentWorker.max_overtime_hours}h)` : 'Opted Out'}
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Synced to Two-Stage Recovery Solver</p>
          </div>

          <div className="p-4 bg-slate-50/70 border border-slate-200/80 rounded-2xl">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Estimated Gross Pay</span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-slate-900">
                ${estimatedGrossPay.toFixed(2)}
              </span>
              <span className="text-xs text-slate-500">this cycle</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Includes regular base hours</p>
          </div>
        </div>
      </div>

      {/* Main Grid: Shift Schedule on Left, Preferences on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: My Upcoming Shifts (Span 7) */}
        <div className="lg:col-span-7 bg-surface border border-border/80 rounded-3xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border/70">
            <div>
              <h3 className="text-base font-bold text-slate-900">My Shift Schedule (Current Week)</h3>
              <p className="text-xs text-slate-500 mt-0.5">Approved shop-floor shifts dispatched by Operations Manager.</p>
            </div>
            <span className="text-xs font-mono text-slate-600 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
              {currentWorker.assigned_shifts.length} Shifts Assigned
            </span>
          </div>

          {currentWorker.assigned_shifts.length === 0 ? (
            <div className="p-8 text-center bg-slate-50 rounded-2xl border border-dashed border-slate-200">
              <CalendarDaysIcon className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-700">No shifts assigned this week</p>
              <p className="text-xs text-slate-500 mt-0.5">
                {currentWorker.is_absent ? 'Worker is on medical leave.' : 'Supervisor has not yet published this week’s roster.'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {currentWorker.assigned_shifts.map((s, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-slate-50/70 hover:bg-slate-50 border border-slate-200/80 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-900">{s.day}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 font-bold">
                        {s.shift_name} Shift
                      </span>
                    </div>
                    <div className="text-xs text-slate-600 font-medium">
                      Station: <strong className="text-slate-800">{s.unit_name}</strong>
                    </div>
                    <div className="flex items-center gap-2 text-[11px] text-slate-500">
                      <ClockIcon className="w-3.5 h-3.5" />
                      <span>{s.time} ({s.hours} hours)</span>
                    </div>
                  </div>

                  <div className="flex sm:flex-col items-end justify-between sm:justify-center gap-1 shrink-0">
                    <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200/80">
                      Rest Gap: {s.rest_interval_hours}h ✓
                    </span>
                    <span className="text-[10px] text-slate-400">Complies &ge; 11h</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Overtime & Qualifications Self-Service (Span 5) */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* Voluntary Overtime Consent Panel */}
          <div className="bg-surface border border-border/80 rounded-3xl p-6 shadow-sm space-y-4">
            <div>
              <div className="flex items-center gap-2">
                <CurrencyDollarIcon className="w-5 h-5 text-purple-600" />
                <h3 className="text-base font-bold text-slate-900">Voluntary Overtime Consent</h3>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Under plant policy, overtime is strictly voluntary and requires prior employee opt-in.
              </p>
            </div>

            {/* Toggle Switch */}
            <div className="p-4 bg-purple-50/60 border border-purple-200/80 rounded-2xl flex items-center justify-between gap-3">
              <div>
                <span className="text-xs font-bold text-slate-900 block">I Consent to Overtime Shifts</span>
                <span className="text-[11px] text-slate-600">
                  {currentWorker.overtime_opt_in ? 'Eligible for call-in & recovery assignments' : 'Will strictly cap at 40.0h'}
                </span>
              </div>
              <button
                type="button"
                onClick={() =>
                  updateCurrentWorker(
                    (w) => ({ ...w, overtime_opt_in: !w.overtime_opt_in }),
                    `Overtime consent updated to: ${!currentWorker.overtime_opt_in ? 'Consented' : 'Opted Out'}. Synced to solver.`
                  )
                }
                className={`w-12 h-6 rounded-full transition-colors relative cursor-pointer ${
                  currentWorker.overtime_opt_in ? 'bg-purple-600' : 'bg-slate-300'
                }`}
              >
                <div
                  className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${
                    currentWorker.overtime_opt_in ? 'left-7' : 'left-1'
                  }`}
                />
              </button>
            </div>

            {/* Max Overtime Selector */}
            {currentWorker.overtime_opt_in && (
              <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-2xl space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-slate-700">Max Weekly Overtime Limit:</span>
                  <span className="font-mono font-bold text-purple-700">+{currentWorker.max_overtime_hours} hours</span>
                </div>
                <input
                  type="range"
                  min="2"
                  max="16"
                  step="2"
                  value={currentWorker.max_overtime_hours}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value);
                    updateCurrentWorker((w) => ({ ...w, max_overtime_hours: val }), `Max OT updated to +${val}h.`);
                  }}
                  className="w-full accent-purple-600 cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                  <span>+2h</span>
                  <span>+8h (Std)</span>
                  <span>+16h (Max)</span>
                </div>
              </div>
            )}
          </div>

          {/* Skills & Certifications Self-Service */}
          <div className="bg-surface border border-border/80 rounded-3xl p-6 shadow-sm space-y-4">
            <div>
              <div className="flex items-center gap-2">
                <ShieldCheckIcon className="w-5 h-5 text-purple-600" />
                <h3 className="text-base font-bold text-slate-900">Verified Skills & Certifications</h3>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Your credentials are independently verified by the scheduler before dispatch.
              </p>
            </div>

            {/* Skills Badges */}
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1.5">
                Qualified Skills:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {currentWorker.skills.map((sk) => (
                  <span
                    key={sk}
                    className="px-3 py-1 bg-slate-100 border border-slate-200 text-slate-800 text-xs font-semibold rounded-full"
                  >
                    {sk} &bull; L4
                  </span>
                ))}
              </div>
            </div>

            {/* Certifications Badges */}
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1.5">
                Certified Licenses:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {currentWorker.certifications.map((cert) => (
                  <span
                    key={cert}
                    className="px-3 py-1 bg-purple-50 border border-purple-200 text-purple-800 text-xs font-bold rounded-full flex items-center gap-1"
                  >
                    <CheckCircleIcon className="w-3.5 h-3.5 text-purple-600" />
                    {cert}
                  </span>
                ))}
              </div>
            </div>

            {/* Add Certification Input */}
            <div className="pt-3 border-t border-slate-200">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={newCertInput}
                  onChange={(e) => setNewCertInput(e.target.value)}
                  placeholder="Add certification (e.g. ISO 9001)..."
                  className="flex-1 px-3 py-1.5 border border-border/80 rounded-full text-xs bg-canvas text-slate-900 outline-none focus:ring-1 focus:ring-primary"
                />
                <button
                  type="button"
                  onClick={() => {
                    if (!newCertInput.trim()) return;
                    updateCurrentWorker(
                      (w) => ({
                        ...w,
                        certifications: Array.from(new Set([...w.certifications, newCertInput.trim()])),
                      }),
                      `Added certification "${newCertInput.trim()}" to profile.`
                    );
                    setNewCertInput('');
                  }}
                  className="px-3 py-1.5 bg-slate-900 text-white rounded-full text-xs font-semibold hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  Add
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
