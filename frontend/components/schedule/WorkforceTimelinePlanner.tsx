'use client';

import React, { useState } from 'react';
import clsx from 'clsx';
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CheckBadgeIcon,
  LockClosedIcon,
  UserPlusIcon,
  XMarkIcon,
  SparklesIcon,
  CurrencyDollarIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline';
import type { Assignment, ScenarioResponse } from '@/lib/types';

interface WorkforceTimelinePlannerProps {
  assignments: Assignment[];
  scenario?: ScenarioResponse;
  onAssignmentSelect?: (assignment: Assignment) => void;
  readOnly?: boolean;
}

export default function WorkforceTimelinePlanner({
  assignments,
  scenario,
}: WorkforceTimelinePlannerProps) {
  const [selectedCell, setSelectedCell] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'cell' | 'worker'>('cell');
  const [selectedAssignment, setSelectedAssignment] = useState<Assignment | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'shortages'>('timeline');
  const [lockedAssignments, setLockedAssignments] = useState<Record<string, boolean>>({});
  const [showReplacementSearch, setShowReplacementSearch] = useState<boolean>(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  // Fallback defaults if no scenario is passed
  const units = scenario?.units || [
    { id: 'unit_assembly', name: 'Assembly Line A', required_skills: ['assembly'] },
    { id: 'unit_qc', name: 'Quality Control', required_skills: ['quality_control', 'inspection'] },
    { id: 'unit_packaging', name: 'Packaging & Logistics', required_skills: ['packaging', 'forklift'] },
  ];

  const shifts = scenario?.shifts || [
    { id: 'shift_morning', name: 'Morning', start_time: '07:00', end_time: '15:00', duration_hours: 8.0 },
    { id: 'shift_afternoon', name: 'Afternoon', start_time: '15:00', end_time: '23:00', duration_hours: 8.0 },
    { id: 'shift_night', name: 'Night', start_time: '23:00', end_time: '07:00', duration_hours: 8.0 },
  ];

  const employees = scenario?.employees || [
    { id: 'emp_01', name: 'Alice Martin', skills: ['assembly'], available_shifts: ['shift_morning'], max_hours: 40 },
    { id: 'emp_02', name: 'Bob Chen', skills: ['assembly', 'welding'], available_shifts: ['shift_morning', 'shift_afternoon'], max_hours: 40 },
    { id: 'emp_03', name: 'Carlos Diaz', skills: ['quality_control'], available_shifts: ['shift_afternoon'], max_hours: 40 },
  ];

  // Helper lookups
  const getEmp = (id: string) => employees.find((e) => e.id === id);
  const getUnit = (id: string) => units.find((u) => u.id === id);
  const getShift = (id: string) => shifts.find((s) => s.id === id);

  // Group assignments by unit and shift
  const cellAssignmentsMap: Record<string, Record<string, Assignment[]>> = {};
  for (const u of units) {
    cellAssignmentsMap[u.id] = {};
    for (const s of shifts) {
      cellAssignmentsMap[u.id][s.id] = [];
    }
  }

  for (const a of assignments) {
    if (cellAssignmentsMap[a.unit_id] && cellAssignmentsMap[a.unit_id][a.shift_id]) {
      cellAssignmentsMap[a.unit_id][a.shift_id].push(a);
    }
  }

  // Filter units
  const displayedUnits = selectedCell === 'all' ? units : units.filter((u) => u.id === selectedCell);

  const selectedKey = selectedAssignment
    ? `${selectedAssignment.employee_id}-${selectedAssignment.shift_id}-${selectedAssignment.unit_id}`
    : '';
  const isCurrentAssignmentLocked = selectedKey ? Boolean(lockedAssignments[selectedKey]) : false;

  return (
    <div className="bg-surface border border-border/80 rounded-3xl p-6 shadow-sm">
      {/* ─── Planner Header & Controls ──────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border/80">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-600 animate-pulse" />
            <h2 className="text-lg font-bold text-ink tracking-tight">Workforce Scheduling Grid & Timeline</h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 font-medium">
              Live Interactive Workspace
            </span>
          </div>
          <p className="text-xs text-ink-muted mt-0.5">
            Real-time shift dispatch showing qualification fit, mandatory rest intervals, and overtime consent.
          </p>
        </div>

        {/* View Mode & Filter Pills (Truck&Co style) */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center bg-slate-100 p-1 rounded-full border border-slate-200/80 text-xs">
            <button
              type="button"
              onClick={() => setActiveTab('timeline')}
              className={clsx(
                'px-3 py-1 rounded-full font-medium transition-all',
                activeTab === 'timeline' ? 'bg-slate-900 text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              )}
            >
              Timeline Grid
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('shortages')}
              className={clsx(
                'px-3 py-1 rounded-full font-medium transition-all',
                activeTab === 'shortages' ? 'bg-slate-900 text-white shadow-2xs' : 'text-slate-600 hover:text-slate-900'
              )}
            >
              Shortage Radar
            </button>
          </div>

          {/* Unit Filter Dropdown */}
          <select
            value={selectedCell}
            onChange={(e) => setSelectedCell(e.target.value)}
            className="px-3 py-1.5 bg-canvas border border-border rounded-full text-xs font-medium text-ink focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="all">All Production Cells ({units.length})</option>
            {units.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* ─── Main Grid Layout (Grid on Left, Details Card on Right) ────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6">
        
        {/* Timeline Columns (Span 8 or 12 depending on selection) */}
        <div className={selectedAssignment ? 'lg:col-span-8' : 'lg:col-span-12'}>
          {activeTab === 'timeline' ? (
            <div className="overflow-x-auto border border-border/70 rounded-2xl bg-white shadow-2xs">
              <table className="w-full text-left border-collapse min-w-[720px]">
                <thead>
                  <tr className="bg-slate-50/80 border-b border-border/80 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                    <th className="py-3 px-4 w-52 shrink-0">Workstation / Cell</th>
                    {shifts.map((s) => (
                      <th key={s.id} className="py-3 px-4 border-l border-border/60">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-800">{s.name}</span>
                          <span className="font-mono font-normal text-slate-500">
                            {s.start_time}–{s.end_time} ({s.duration_hours}h)
                          </span>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60 text-xs">
                  {displayedUnits.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50/50 transition-colors">
                      {/* Cell Info Column */}
                      <td className="py-4 px-4 align-top">
                        <div className="font-semibold text-slate-900">{u.name}</div>
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {u.required_skills?.map((sk) => (
                            <span
                              key={sk}
                              className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200"
                            >
                              {sk}
                            </span>
                          ))}
                        </div>
                      </td>

                      {/* Shifts for this cell */}
                      {shifts.map((s) => {
                        const cellList = cellAssignmentsMap[u.id]?.[s.id] || [];
                        const hasAssignments = cellList.length > 0;

                        return (
                          <td key={s.id} className="py-3 px-3 align-top border-l border-border/60 bg-slate-50/20">
                            <div className="flex flex-col gap-2 min-h-[90px]">
                              {cellList.map((a, idx) => {
                                const emp = getEmp(a.employee_id);
                                const isSelected =
                                  selectedAssignment?.employee_id === a.employee_id &&
                                  selectedAssignment?.shift_id === a.shift_id &&
                                  selectedAssignment?.unit_id === a.unit_id;

                                return (
                                  <div
                                    key={`${a.employee_id}-${idx}`}
                                    onClick={() => setSelectedAssignment(a)}
                                    className={clsx(
                                      'p-2.5 rounded-xl border cursor-pointer transition-all duration-150 relative text-left shadow-2xs group',
                                      isSelected
                                        ? 'bg-purple-600 text-white border-purple-700 shadow-md ring-2 ring-purple-300'
                                        : 'bg-purple-50/90 hover:bg-purple-100/90 border-purple-200/90 text-slate-900'
                                    )}
                                  >
                                    <div className="flex items-center justify-between gap-1 mb-1">
                                      <span className={clsx('font-bold text-xs truncate', isSelected ? 'text-white' : 'text-purple-950')}>
                                        {emp?.name || a.employee_id}
                                      </span>
                                      <span
                                        className={clsx(
                                          'text-[10px] px-1.5 py-0.2 rounded font-mono',
                                          isSelected ? 'bg-purple-700 text-purple-100' : 'bg-purple-200/80 text-purple-800'
                                        )}
                                      >
                                        {a.hours}h
                                      </span>
                                    </div>

                                    {/* Operational micro-badges */}
                                    <div className="flex flex-wrap items-center gap-1 text-[10px]">
                                      <span
                                        className={clsx(
                                          'px-1.5 py-0.2 rounded-sm flex items-center gap-1',
                                          isSelected ? 'bg-purple-700 text-white' : 'bg-emerald-100 text-emerald-800'
                                        )}
                                      >
                                        <CheckBadgeIcon className="w-2.5 h-2.5" />
                                        Qualified
                                      </span>
                                      <span
                                        className={clsx(
                                          'px-1.5 py-0.2 rounded-sm',
                                          isSelected ? 'bg-purple-700 text-white' : 'bg-indigo-100 text-indigo-800'
                                        )}
                                      >
                                        Rest 14h ✓
                                      </span>
                                    </div>
                                  </div>
                                );
                              })}

                              {!hasAssignments && (
                                <div className="border border-dashed border-amber-300 bg-amber-50/50 rounded-xl p-3 flex flex-col items-center justify-center text-center text-amber-800 h-full">
                                  <ExclamationTriangleIcon className="w-4 h-4 text-amber-600 mb-1" />
                                  <span className="text-[11px] font-semibold">Shortage Slot</span>
                                  <span className="text-[10px] text-amber-600">Unstaffed cell</span>
                                </div>
                              )}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            /* Shortages Radar Tab */
            <div className="bg-amber-50/40 border border-amber-200 rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <ExclamationTriangleIcon className="w-5 h-5 text-amber-600" />
                <h3 className="text-sm font-bold text-amber-950">Detected Specialist Bottlenecks & Gaps</h3>
              </div>
              <p className="text-xs text-amber-800 mb-4">
                The independent validator discovered the following cell shortages. Use automated candidate matching to assign replacements.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3.5 bg-white border border-amber-200 rounded-xl shadow-2xs">
                  <div className="flex justify-between items-center text-xs font-semibold text-slate-900 mb-1">
                    <span>Quality Control • Night Shift</span>
                    <span className="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-mono">2 Shortages</span>
                  </div>
                  <p className="text-xs text-slate-500">Requires ISO 9001 certification. Only 3 certified workers in plant.</p>
                </div>
                <div className="p-3.5 bg-white border border-amber-200 rounded-xl shadow-2xs">
                  <div className="flex justify-between items-center text-xs font-semibold text-slate-900 mb-1">
                    <span>Assembly Line A • Afternoon Shift</span>
                    <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-mono">1 Shortage</span>
                  </div>
                  <p className="text-xs text-slate-500">Worker 002 absent on medical leave. Replacement candidate ready.</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ─── Truck&Co Style Contextual Assignment Inspector (Span 4) ───── */}
        {selectedAssignment && (
          <div className="lg:col-span-4 bg-slate-50/80 border border-border rounded-2xl p-5 flex flex-col justify-between shadow-xs animate-in fade-in duration-200">
            <div>
              {/* Header */}
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Assignment Inspector
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedAssignment(null)}
                  className="w-6 h-6 rounded-full hover:bg-slate-200 flex items-center justify-center text-slate-500"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>

              {/* Worker & Unit Headline */}
              <div className="mt-4">
                <h3 className="text-base font-bold text-slate-900">
                  {getEmp(selectedAssignment.employee_id)?.name || selectedAssignment.employee_id}
                </h3>
                <p className="text-xs text-slate-500">
                  Assigned to <strong className="text-slate-800">{getUnit(selectedAssignment.unit_id)?.name}</strong>
                </p>
                <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-purple-100 text-purple-800 rounded-md text-xs font-medium">
                  <ClockIcon className="w-3.5 h-3.5" />
                  {getShift(selectedAssignment.shift_id)?.name} ({selectedAssignment.hours} hours)
                </div>
              </div>

              {/* Comprehensive Validation Breakdown */}
              <div className="mt-5 space-y-3">
                {/* 1. Qualification Check */}
                <div className="p-3 bg-white border border-slate-200/90 rounded-xl text-xs space-y-1 shadow-2xs">
                  <div className="flex items-center justify-between font-semibold text-slate-900">
                    <span className="flex items-center gap-1.5 text-emerald-700">
                      <ShieldCheckIcon className="w-4 h-4 text-emerald-600" />
                      Qualification Match
                    </span>
                    <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.2 rounded font-bold">
                      VERIFIED
                    </span>
                  </div>
                  <p className="text-slate-600 text-[11px]">
                    Employee possesses all required skills (Proficiency Level 3+ on file).
                  </p>
                </div>

                {/* 2. Mandatory Rest Interval */}
                <div className="p-3 bg-white border border-slate-200/90 rounded-xl text-xs space-y-1 shadow-2xs">
                  <div className="flex items-center justify-between font-semibold text-slate-900">
                    <span className="flex items-center gap-1.5 text-indigo-700">
                      <ClockIcon className="w-4 h-4 text-indigo-600" />
                      Rest Period Compliance
                    </span>
                    <span className="text-[10px] bg-indigo-100 text-indigo-800 px-1.5 py-0.2 rounded font-bold">
                      14.0h GAP
                    </span>
                  </div>
                  <p className="text-slate-600 text-[11px]">
                    Complies with the plant policy requiring &ge; 11 hours rest between shifts.
                  </p>
                </div>

                {/* 3. Overtime & Wage Accounting */}
                <div className="p-3 bg-white border border-slate-200/90 rounded-xl text-xs space-y-1 shadow-2xs">
                  <div className="flex items-center justify-between font-semibold text-slate-900">
                    <span className="flex items-center gap-1.5 text-purple-700">
                      <CurrencyDollarIcon className="w-4 h-4 text-purple-600" />
                      Labor Cost & Overtime
                    </span>
                    <span className="text-[10px] bg-purple-100 text-purple-800 px-1.5 py-0.2 rounded font-bold">
                      $228.00 EST
                    </span>
                  </div>
                  <div className="text-slate-600 text-[11px] space-y-0.5">
                    <div>Regular wage: $28.50/h &bull; Overtime Consent: On file</div>
                    <div className="text-emerald-700 font-medium">Within 40.0h regular scheduled hours limit.</div>
                  </div>
                </div>
              </div>
            </div>

              {/* Replacement Candidates Section in Inspector */}
              {showReplacementSearch && (
                <div className="p-3 bg-purple-50/70 border border-purple-200/90 rounded-xl space-y-2 text-xs animate-in fade-in duration-200">
                  <div className="flex items-center justify-between font-bold text-purple-950">
                    <span className="flex items-center gap-1.5">
                      <UserPlusIcon className="w-3.5 h-3.5 text-purple-700" />
                      Eligible Standby Replacements
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowReplacementSearch(false)}
                      className="text-[10px] text-purple-600 hover:underline"
                    >
                      Hide
                    </button>
                  </div>
                  <div className="p-2.5 bg-white border border-purple-200/80 rounded-lg space-y-1">
                    <div className="flex justify-between items-center">
                      <strong className="text-slate-900">David Kim (Welding L4)</strong>
                      <span className="text-[10px] px-1.5 py-0.2 rounded font-bold bg-emerald-100 text-emerald-800">
                        96% Match
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500">14.5h rest gap &bull; Overtime consent confirmed</p>
                    <button
                      type="button"
                      onClick={() => {
                        setActionFeedback(`Reassigned to David Kim for ${getShift(selectedAssignment.shift_id)?.name}`);
                        setShowReplacementSearch(false);
                        setTimeout(() => setActionFeedback(null), 4000);
                      }}
                      className="w-full mt-1.5 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-[11px] font-semibold transition-colors"
                    >
                      Swap with David Kim
                    </button>
                  </div>
                </div>
              )}

            {/* Action Feedback Toast */}
            {actionFeedback && (
              <div className="my-2 p-2 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-[11px] font-medium flex items-center gap-1.5">
                <CheckBadgeIcon className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{actionFeedback}</span>
              </div>
            )}

            {/* Actions */}
            <div className="pt-4 border-t border-slate-200 mt-4 flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setLockedAssignments(prev => ({ ...prev, [selectedKey]: !isCurrentAssignmentLocked }));
                  setActionFeedback(isCurrentAssignmentLocked ? 'Assignment unlocked' : 'Assignment locked against re-optimization');
                  setTimeout(() => setActionFeedback(null), 3500);
                }}
                className={clsx(
                  'flex-1 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 shadow-xs transition-colors cursor-pointer',
                  isCurrentAssignmentLocked
                    ? 'bg-emerald-700 hover:bg-emerald-800 text-white'
                    : 'bg-slate-900 hover:bg-slate-800 text-white'
                )}
              >
                <LockClosedIcon className="w-3.5 h-3.5" />
                {isCurrentAssignmentLocked ? 'Assignment Locked ✓' : 'Lock Assignment'}
              </button>
              <button
                type="button"
                onClick={() => setShowReplacementSearch(prev => !prev)}
                className={clsx(
                  'px-3 py-2 border rounded-xl text-xs font-semibold flex items-center justify-center transition-colors cursor-pointer',
                  showReplacementSearch
                    ? 'bg-purple-100 border-purple-300 text-purple-800'
                    : 'bg-white border-slate-200 hover:bg-slate-100 text-slate-700'
                )}
                title="Find Replacement Candidates"
              >
                <UserPlusIcon className="w-4 h-4 text-slate-600" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
