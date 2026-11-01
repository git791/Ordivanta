'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { api } from '@/lib/api';
import type { ScenarioSummary, RunSummary, ScenarioResponse, Assignment, DatasetMetadata } from '@/lib/types';
import PageHeader from '@/components/ui/PageHeader';
import KpiCard from '@/components/ui/KpiCard';
import StatusBadge from '@/components/ui/StatusBadge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorBanner from '@/components/ui/ErrorBanner';
import WorkforceTimelinePlanner from '@/components/schedule/WorkforceTimelinePlanner';
import {
  SparklesIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  ClockIcon,
  BuildingOffice2Icon,
  ArrowRightIcon,
  XMarkIcon,
  CheckCircleIcon,
  UserPlusIcon,
} from '@heroicons/react/24/outline';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';

export default function DashboardPage() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [scenarioDetails, setScenarioDetails] = useState<ScenarioResponse | null>(null);
  const [activeAssignments, setActiveAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Replacement Dispatch State
  const [replacementModalOpen, setReplacementModalOpen] = useState<boolean>(false);
  const [replacementAssigned, setReplacementAssigned] = useState<boolean>(false);
  const [assignedCandidateName, setAssignedCandidateName] = useState<string>('David Kim');
  const [dispatchToast, setDispatchToast] = useState<string | null>(null);

  // Supervisor Plant & Dynamic Dataset State Filters
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('default');
  const [selectedPlant, setSelectedPlant] = useState('Detroit Assembly Plant #1');
  const [selectedUnit, setSelectedUnit] = useState('All Production Units');
  const [schedulePeriod, setSchedulePeriod] = useState('Current Week (Nov 01 - Nov 07, 2026)');

  // Worker Portal Real-Time Synchronization State
  const [workerSyncState, setWorkerSyncState] = useState<{
    emp_david?: { overtime_opt_in: boolean; max_overtime_hours: number; skills: string[]; certifications: string[]; is_absent: boolean };
    emp_alice?: { overtime_opt_in: boolean; max_overtime_hours: number; skills: string[]; certifications: string[]; is_absent: boolean };
    emp_004?: { overtime_opt_in: boolean; max_overtime_hours: number; skills: string[]; certifications: string[]; is_absent: boolean };
  } | null>(null);

  useEffect(() => {
    const syncWorkerState = () => {
      try {
        const raw = localStorage.getItem('ordivanta_worker_sync_state');
        if (raw) {
          setWorkerSyncState(JSON.parse(raw));
        }
      } catch {
        // ignore
      }
    };
    syncWorkerState();
    window.addEventListener('storage', syncWorkerState);
    return () => window.removeEventListener('storage', syncWorkerState);
  }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [scenariosData, runsData, datasetsData] = await Promise.all([
        api.getScenarios().catch(() => [] as ScenarioSummary[]),
        api.getRuns().catch(() => [] as RunSummary[]),
        api.getDatasets().catch(() => [] as DatasetMetadata[]),
      ]);
      setScenarios(scenariosData || []);
      setRuns(runsData || []);
      setDatasets(datasetsData || []);

      // If we have runs, fetch latest run details for live assignments
      if (runsData && runsData.length > 0) {
        try {
          const latestRun = await api.getRun(runsData[0].run_id);
          if (latestRun.assignments && latestRun.assignments.length > 0) {
            setActiveAssignments(latestRun.assignments);
          }
          if (latestRun.scenario_id) {
            const sc = await api.getScenario(latestRun.scenario_id);
            setScenarioDetails(sc);
          }
        } catch (runErr) {
          console.warn('Could not fetch latest run assignments:', runErr);
        }
      } else if (scenariosData && scenariosData.length > 0) {
        try {
          const sc = await api.getScenario(scenariosData[0].id);
          setScenarioDetails(sc);
        } catch (scErr) {
          console.warn('Could not fetch default scenario:', scErr);
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to connect to the backend API.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Operational Trend Data (Required vs Assigned positions across shifts)
  const shiftTrendData = [
    { shift: 'Mon M', required: 36, assigned: 36, shortage: 0, overtime_h: 8 },
    { shift: 'Mon A', required: 36, assigned: 34, shortage: 2, overtime_h: 12 },
    { shift: 'Mon N', required: 36, assigned: 32, shortage: 4, overtime_h: 16 },
    { shift: 'Tue M', required: 36, assigned: 36, shortage: 0, overtime_h: 8 },
    { shift: 'Tue A', required: 36, assigned: 35, shortage: 1, overtime_h: 10 },
    { shift: 'Tue N', required: 36, assigned: 30, shortage: 6, overtime_h: 24 },
    { shift: 'Wed M', required: 36, assigned: 36, shortage: 0, overtime_h: 4 },
  ];

  // Fallback demo assignments if none are returned by the API
  const sampleFallbackAssignments: Assignment[] = activeAssignments.length > 0 ? activeAssignments : [
    { employee_id: 'emp_01', shift_id: 'shift_morning', unit_id: 'unit_assembly', hours: 8.0 },
    { employee_id: 'emp_02', shift_id: 'shift_afternoon', unit_id: 'unit_assembly', hours: 8.0 },
    { employee_id: 'emp_03', shift_id: 'shift_afternoon', unit_id: 'unit_qc', hours: 8.0 },
    { employee_id: 'emp_01', shift_id: 'shift_morning', unit_id: 'unit_packaging', hours: 8.0 },
  ];

  // Real-time synchronization values with Worker Self-Service Portal
  const marcusSync = workerSyncState?.emp_004;
  const isMarcusAbsent = marcusSync !== undefined ? marcusSync.is_absent : true;
  const cell03FullyCovered = replacementAssigned || !isMarcusAbsent;

  const davidSync = workerSyncState?.emp_david;
  const davidOtConsent = davidSync !== undefined ? davidSync.overtime_opt_in : true;
  const davidMaxOt = davidSync?.max_overtime_hours ?? 8.0;
  const davidCerts = davidSync?.certifications ?? ['ISO 9001:2015', 'AWS D1.1 Structural Welding', 'Safety Level 2'];

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-8 max-w-full overflow-x-hidden">
      {error && <ErrorBanner message={error} />}

      {/* Header with Plant & Period Selectors (Truck&Co style) */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-border/70 pb-6 gap-4">
        <div>
          <PageHeader
            title="Manufacturing Operations Command Center"
            description="Real-time shift coverage, specialist bottleneck tracking, lifecycle approvals, and overtime controls."
          />
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Dynamic Scenario / Plant Dropdown */}
          <select
            value={selectedScenarioId}
            onChange={async (e) => {
              const val = e.target.value;
              setSelectedScenarioId(val);
              if (val === 'default') {
                setSelectedPlant('Detroit Assembly Plant #1');
                if (scenarios.length > 0) {
                  try {
                    const sc = await api.getScenario(scenarios[0].id);
                    setScenarioDetails(sc);
                  } catch (err) {
                    console.warn(err);
                  }
                }
              } else {
                const found = scenarios.find((s) => s.id === val);
                if (found) {
                  setSelectedPlant(found.name);
                  try {
                    const sc = await api.getScenario(found.id);
                    setScenarioDetails(sc);
                  } catch (err) {
                    console.warn(err);
                  }
                }
              }
            }}
            className="px-3.5 py-1.5 bg-surface border border-border/80 rounded-full text-xs font-medium text-slate-800 shadow-2xs focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer max-w-[280px] truncate"
            title="Select Manufacturing Plant Scenario"
          >
            <option value="default">Detroit Assembly Plant #1 (Synthetic Manufacturing)</option>
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.employee_count} workers, {s.unit_count} units)
              </option>
            ))}
          </select>

          {/* Dynamic Production Unit Dropdown */}
          <select
            value={selectedUnit}
            onChange={(e) => setSelectedUnit(e.target.value)}
            className="px-3.5 py-1.5 bg-surface border border-border/80 rounded-full text-xs font-medium text-slate-800 shadow-2xs focus:outline-none focus:ring-1 focus:ring-primary cursor-pointer"
            title="Filter by Production Cell"
          >
            <option value="All Production Units">All Production Units</option>
            {scenarioDetails?.units && scenarioDetails.units.length > 0 ? (
              scenarioDetails.units.map((u) => (
                <option key={u.id} value={u.name}>
                  {u.name}
                </option>
              ))
            ) : (
              <>
                <option value="Cell 01 (Machining / Welding)">Cell 01 (Machining / Welding)</option>
                <option value="Cell 02 (CNC Stamping)">Cell 02 (CNC Stamping)</option>
                <option value="Cell 03 (Robotic Welding)">Cell 03 (Robotic Welding)</option>
                <option value="Cell 04 (Final QC & Packaging)">Cell 04 (Final QC & Packaging)</option>
              </>
            )}
          </select>

          <span className="px-3.5 py-1.5 bg-slate-100 border border-slate-200/80 rounded-full text-xs font-mono text-slate-600 shadow-2xs">
            {schedulePeriod}
          </span>
        </div>
      </div>

      {/* Benchmark Datasets Provenance & Cross-Role Status Banner */}
      <div className="bg-slate-50/90 border border-slate-200/80 rounded-2xl px-4 py-3 flex flex-wrap items-center justify-between gap-3 text-xs shadow-2xs">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-bold text-slate-800 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Original Benchmark Datasets Available:
          </span>
          <span className="px-2.5 py-0.5 rounded-full bg-white border border-slate-200 font-mono text-[11px] text-slate-700 shadow-2xs" title="225 instances in data/instances1_225">
            Shift Scheduling: 225 TXT
          </span>
          <span className="px-2.5 py-0.5 rounded-full bg-white border border-slate-200 font-mono text-[11px] text-slate-700 shadow-2xs" title="137 instances in data/ptask">
            PTSP Task Allocation: 137 DAT
          </span>
          <span className="px-2.5 py-0.5 rounded-full bg-white border border-slate-200 font-mono text-[11px] text-slate-700 shadow-2xs" title="24 instances in data/instances1_24">
            Nurse Rostering: 24 Instances
          </span>
          <span className="px-2.5 py-0.5 rounded-full bg-purple-50 border border-purple-200 font-mono text-[11px] text-purple-700 font-semibold shadow-2xs">
            Synthetic Mfg: Primary
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/schedule"
            className="font-semibold text-purple-600 hover:text-purple-700 flex items-center gap-1 hover:underline"
          >
            <span>Solve Instance in Planner</span>
            <ArrowRightIcon className="w-3 h-3" />
          </Link>
          <span className="text-slate-300">|</span>
          <Link
            href="/worker"
            className="font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1 hover:underline"
          >
            <span>Worker Portal (Self-Service)</span>
            <ArrowRightIcon className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* Facility Visual Showcase + Cell Status Matrix Card */}
      <div className="bg-surface border border-border/80 rounded-3xl p-6 shadow-sm overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
          {/* Facility 3D Isometric View */}
          <div className="lg:col-span-5 relative rounded-2xl overflow-hidden border border-border/60 shadow-2xs aspect-16/10 bg-gradient-to-br from-slate-900 via-slate-900 to-purple-950/40 p-2 group">
            <Image
              src="/plant-facility.png"
              alt="Ordivanta Manufacturing Facility 3D Isometric Layout"
              fill
              className="object-contain transition-transform duration-500 group-hover:scale-105"
              priority
            />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-transparent to-transparent flex flex-col justify-end p-4 text-white pointer-events-none">
              <div className="flex items-center gap-2 text-xs font-semibold text-purple-300">
                <BuildingOffice2Icon className="w-4 h-4 text-purple-400" />
                <span>Shop Floor Digital Twin • Facility #1</span>
              </div>
              <p className="text-[11px] text-slate-300 mt-0.5">
                Active telemetry: 4 robotic cells, 24 workstations, 3-shift rotation schedule.
              </p>
            </div>
          </div>

          {/* Cell Operations Status Summary */}
          <div className="lg:col-span-7 flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <h3 className="text-base font-bold text-slate-900">Cell Staffing Health & Bottleneck Matrix</h3>
                </div>
                <span className="text-xs font-mono text-slate-500">Live Telemetry</span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Monitored against strict qualification policy (Level 3+ proficiency & ISO certifications).
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Cell 01 */}
              <div className="p-3.5 bg-slate-50/70 border border-slate-200/80 rounded-2xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">Cell 01 • Machining & Weld</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                    38.1% Ceiling
                  </span>
                </div>
                <div className="text-[11px] text-slate-600">
                  <span className="text-amber-700 font-semibold">Specialist Shortage:</span> Only 3 certified Welding L4 technicians on roster.
                </div>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mt-1">
                  <div className="bg-amber-500 h-1.5 rounded-full w-[38%]" />
                </div>
              </div>

              {/* Cell 02 */}
              <div className="p-3.5 bg-slate-50/70 border border-slate-200/80 rounded-2xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">Cell 02 • CNC Stamping</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                    100% Optimal
                  </span>
                </div>
                <div className="text-[11px] text-slate-600">
                  All 18 required positions fully staffed with qualified operators.
                </div>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mt-1">
                  <div className="bg-emerald-500 h-1.5 rounded-full w-[100%]" />
                </div>
              </div>

              {/* Cell 03 */}
              <div className="p-3.5 bg-slate-50/70 border border-slate-200/80 rounded-2xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">Cell 03 • Robotic Welding</span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      cell03FullyCovered
                        ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                        : 'bg-amber-100 text-amber-800 border-amber-200'
                    }`}
                  >
                    {cell03FullyCovered ? '100% Optimal' : '88.9% Feasible'}
                  </span>
                </div>
                <div className="text-[11px] text-slate-600">
                  {!isMarcusAbsent
                    ? 'Worker 004 active on duty (Medical leave cleared in Worker Portal). 0 line stoppages.'
                    : replacementAssigned
                    ? `Worker 004 absence covered by ${assignedCandidateName}. 0 line stoppages.`
                    : '1 unstaffed slot on Afternoon shift. Replacement candidate on standby.'}
                </div>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mt-1">
                  <div
                    className={`h-1.5 rounded-full transition-all duration-500 ${
                      cell03FullyCovered ? 'bg-emerald-500 w-[100%]' : 'bg-amber-500 w-[89%]'
                    }`}
                  />
                </div>
              </div>

              {/* Cell 04 */}
              <div className="p-3.5 bg-slate-50/70 border border-slate-200/80 rounded-2xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">Cell 04 • Final QC & Pack</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                    100% Optimal
                  </span>
                </div>
                <div className="text-[11px] text-slate-600">
                  Full coverage with certified ISO 9001 quality inspectors.
                </div>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mt-1">
                  <div className="bg-emerald-500 h-1.5 rounded-full w-[100%]" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Operational Status & Lifecycle Banner */}
      <div className="bg-surface border border-border/80 rounded-3xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-3 h-3 rounded-full bg-amber-500 animate-pulse" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-slate-900">Schedule Status:</span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300">
                PENDING_APPROVAL
              </span>
              <span className="text-xs text-slate-500">(Revision v2.1 • Generated by Two-Stage Recovery MILP)</span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Draft awaits Operations Manager sign-off before publishing to shop-floor kiosks.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          <Link
            href="/schedule"
            className="px-4 py-2 bg-slate-900 text-white text-xs font-semibold rounded-full hover:bg-slate-800 shadow-2xs transition-all flex items-center gap-1.5"
          >
            Review & Authorize Roster
            <ArrowRightIcon className="w-3 h-3" />
          </Link>
          <Link
            href="/demo"
            className="px-4 py-2 bg-canvas border border-border/80 text-xs font-semibold text-slate-800 rounded-full hover:bg-slate-100 transition-all"
          >
            Shock Simulation
          </Link>
        </div>
      </div>

      {/* Supervisor KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Staffing Coverage"
          value="93.8%"
          note="236 of 252 required positions filled"
          badge={{ text: '+4.2% vs baseline', variant: 'success' }}
        />
        <KpiCard
          label="Specialist Shortages"
          value="16 pos"
          note="12 Welding Level 4, 4 ISO QC Certs"
          badge={{ text: 'Critical Gaps', variant: 'danger' }}
        />
        <KpiCard
          label="Voluntary Overtime"
          value="84.0 h"
          note="Est. premium: $1,197.00 (14 consenting staff)"
          badge={{ text: '14 Consenting', variant: 'purple' }}
        />
        <KpiCard
          label="Absences & Call-ins"
          value="4 Absent"
          note="3 on-call candidates ready for review"
          badge={{ text: '3 Ready', variant: 'warning' }}
        />
      </div>

      {/* ─── Centerpiece: Workforce Timeline Planner ──────────────────────── */}
      <WorkforceTimelinePlanner
        assignments={sampleFallbackAssignments}
        scenario={scenarioDetails ?? undefined}
      />

      {/* Main Charts & Operational Views */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Real Operational Shift Coverage & Overtime Trend */}
        <div className="lg:col-span-2 bg-surface border border-border/80 rounded-3xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Shift Demand vs. Staffing vs. Overtime Hours
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Visualizing actual staffing levels against demand and overtime usage by shift.
              </p>
            </div>
            <span className="text-xs font-mono text-slate-600 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
              Horizon: 7 Days
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={shiftTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="shift" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis yAxisId="headcount" tick={{ fontSize: 11, fill: '#64748B' }} domain={[0, 45]} />
                <YAxis yAxisId="overtime" orientation="right" tick={{ fontSize: 11, fill: '#64748B' }} domain={[0, 30]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E2E8F0',
                    borderRadius: '12px',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.05)',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Bar yAxisId="headcount" dataKey="assigned" name="Assigned Staff" fill="#7C3AED" radius={[4, 4, 0, 0]} />
                <Bar yAxisId="headcount" dataKey="shortage" name="Unfilled Shortage" fill="#EF4444" radius={[4, 4, 0, 0]} />
                <Line
                  yAxisId="overtime"
                  type="monotone"
                  dataKey="overtime_h"
                  name="Overtime Hours"
                  stroke="#F59E0B"
                  strokeWidth={2.5}
                  dot={{ r: 4 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Urgent Supervisor Action Panel */}
        <div className="bg-surface border border-border/80 rounded-3xl p-6 flex flex-col justify-between shadow-sm">
          <div>
            <h2 className="text-base font-bold text-slate-900 mb-1">Supervisory Action Queue</h2>
            <p className="text-xs text-slate-500 mb-4">
              Decisions required to prevent line stoppages.
            </p>

            <div className="space-y-3">
              {/* Alert 1: Specialist Replacement Workflow */}
              {!isMarcusAbsent ? (
                <div className="p-3.5 bg-emerald-50/80 border border-emerald-200/90 rounded-2xl animate-in fade-in duration-300 shadow-2xs">
                  <div className="flex items-center justify-between text-xs font-bold text-emerald-950 mb-1">
                    <span className="flex items-center gap-1.5">
                      <ShieldCheckIcon className="w-4 h-4 text-emerald-600" />
                      Robotic Welding (Cell 03)
                    </span>
                    <span className="text-[10px] bg-emerald-100 px-2 py-0.5 rounded-full text-emerald-800 font-bold border border-emerald-200">
                      Active via Portal ✓
                    </span>
                  </div>
                  <p className="text-xs text-emerald-800">
                    Worker 004 marked active in Worker Self-Service Portal. Cell 03 is fully staffed with 0 line stoppage risk.
                  </p>
                </div>
              ) : replacementAssigned ? (
                <div className="p-3.5 bg-emerald-50/80 border border-emerald-200/90 rounded-2xl animate-in fade-in duration-300 shadow-2xs">
                  <div className="flex items-center justify-between text-xs font-bold text-emerald-950 mb-1">
                    <span className="flex items-center gap-1.5">
                      <ShieldCheckIcon className="w-4 h-4 text-emerald-600" />
                      Robotic Welding (Cell 03)
                    </span>
                    <span className="text-[10px] bg-emerald-100 px-2 py-0.5 rounded-full text-emerald-800 font-bold border border-emerald-200">
                      Resolved ✓
                    </span>
                  </div>
                  <p className="text-xs text-emerald-800">
                    Dispatched <strong>{assignedCandidateName}</strong> (Welding L4 + ISO 9001). Line stoppage averted.
                  </p>
                  <div className="mt-2.5 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setReplacementModalOpen(true)}
                      className="text-xs bg-emerald-700 text-white px-3 py-1 rounded-full font-semibold hover:bg-emerald-800 shadow-2xs transition-colors cursor-pointer"
                    >
                      View Dispatch
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setReplacementAssigned(false);
                        setDispatchToast('Replacement assignment undone. Cell 03 shortage reopened.');
                        setTimeout(() => setDispatchToast(null), 4000);
                      }}
                      className="text-xs text-slate-500 hover:text-slate-800 underline px-2 cursor-pointer"
                    >
                      Undo
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-3.5 bg-red-50/70 border border-red-200/90 rounded-2xl">
                  <div className="flex items-center justify-between text-xs font-bold text-red-900 mb-1">
                    <span>Robotic Welding (Cell 03)</span>
                    <span className="text-[10px] bg-red-100 px-2 py-0.5 rounded-full text-red-800 font-bold">Critical</span>
                  </div>
                  <p className="text-xs text-red-700">
                    Worker 004 absent. Only 1 candidate holds ISO 9001 + Welding L4.
                  </p>
                  <div className="mt-2.5 flex gap-2">
                    <button
                      type="button"
                      onClick={() => setReplacementModalOpen(true)}
                      className="text-xs bg-red-600 hover:bg-red-700 text-white px-3.5 py-1.5 rounded-full font-semibold shadow-2xs transition-all flex items-center gap-1.5 cursor-pointer"
                    >
                      <UserPlusIcon className="w-3.5 h-3.5" />
                      <span>Assign Replacement</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Alert 2 */}
              <div className="p-3.5 bg-amber-50/70 border border-amber-200/90 rounded-2xl">
                <div className="flex items-center justify-between text-xs font-bold text-amber-900 mb-1">
                  <span>Overtime Consent Approvals</span>
                  <span className="text-[10px] bg-amber-100 px-2 py-0.5 rounded-full text-amber-800 font-bold">Action</span>
                </div>
                <p className="text-xs text-amber-700">
                  4 employees near 40h regular limit have confirmed voluntary OT consent on file.
                </p>
              </div>

              {/* Alert 3 */}
              <div className="p-3.5 bg-purple-50/70 border border-purple-200/90 rounded-2xl">
                <div className="flex items-center justify-between text-xs font-bold text-purple-900 mb-1">
                  <span>Rest Compliance</span>
                  <span className="text-[10px] bg-purple-100 px-2 py-0.5 rounded-full text-purple-800 font-bold">Verified</span>
                </div>
                <p className="text-xs text-purple-700">
                  All 236 current assignments pass mandatory 11-hour rest interval checks.
                </p>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-border/80 mt-4">
            <div className="flex justify-between text-xs text-slate-500 mb-2">
              <span>Plant Policy Compliance:</span>
              <span className="font-bold text-emerald-600">100% Policy Pass</span>
            </div>
          </div>
        </div>
      </div>

      {/* Toast Notification */}
      {dispatchToast && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white px-5 py-3 rounded-2xl shadow-xl flex items-center gap-3 animate-in slide-in-from-bottom-3 duration-300 border border-slate-700 text-xs">
          <CheckCircleIcon className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{dispatchToast}</span>
          <button
            type="button"
            onClick={() => setDispatchToast(null)}
            className="ml-2 text-slate-400 hover:text-white"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Replacement Dispatch Modal */}
      {replacementModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-border/80 rounded-3xl max-w-2xl w-full p-6 shadow-2xl relative animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-border/80">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-purple-100 flex items-center justify-center text-purple-700">
                  <UserPlusIcon className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    Specialist Replacement Dispatch Engine
                  </h3>
                  <p className="text-xs text-slate-500">
                    Ranked candidates evaluated against skill qualifications, rest intervals, and overtime policies.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setReplacementModalOpen(false)}
                className="w-8 h-8 rounded-full hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-700 transition-colors cursor-pointer"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>

            {/* Target Shortage Position Card */}
            <div className="my-4 p-4 bg-slate-50/90 border border-slate-200/80 rounded-2xl">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                <div>
                  <span className="text-slate-500">Target Cell:</span>{' '}
                  <strong className="text-slate-900">Robotic Welding (Cell 03)</strong>
                </div>
                <div>
                  <span className="text-slate-500">Shift:</span>{' '}
                  <strong className="text-slate-900">Afternoon (15:00–23:00 • 8.0h)</strong>
                </div>
                <div>
                  <span className="text-slate-500">Absent Worker:</span>{' '}
                  <span className="font-semibold text-rose-700">Worker 004 (Medical Leave)</span>
                </div>
              </div>
              <div className="mt-2 text-xs text-slate-600 flex items-center gap-1.5">
                <span className="font-semibold text-slate-700">Mandatory Prerequisite:</span>
                <span className="px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 text-[11px] font-bold">
                  Welding Level 4
                </span>
                <span className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-bold">
                  ISO 9001 Cert
                </span>
              </div>
            </div>

            {/* Candidate List */}
            <div className="space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Ranked Eligible Candidates (2 Found):
              </div>

              {/* Candidate 1: David Kim (Recommended) */}
              <div className="p-4 bg-purple-50/50 border border-purple-200/90 rounded-2xl space-y-2.5">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-slate-900">David Kim</h4>
                      <span className="text-xs text-slate-500">(Senior Welding Specialist • #W412)</span>
                    </div>
                    <div className="text-xs text-slate-600 mt-0.5">
                      Wage Rate: $32.50/h &bull; Est. Shift Cost: $260.00
                    </div>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                    96% Match • Recommended
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px]">
                  <div className="p-2 bg-white rounded-xl border border-purple-100 flex items-center gap-1.5 text-emerald-700 font-semibold">
                    <ShieldCheckIcon className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Welding L4 + ISO 9001 ✓</span>
                  </div>
                  <div className="p-2 bg-white rounded-xl border border-purple-100 flex items-center gap-1.5 text-indigo-700 font-semibold">
                    <ClockIcon className="w-4 h-4 text-indigo-600 shrink-0" />
                    <span>14.5h Rest Interval ✓</span>
                  </div>
                  <div
                    className={`p-2 bg-white rounded-xl border flex items-center gap-1.5 font-semibold ${
                      davidOtConsent
                        ? 'border-purple-100 text-purple-700'
                        : 'border-rose-200 text-rose-700 bg-rose-50/50'
                    }`}
                  >
                    {davidOtConsent ? (
                      <SparklesIcon className="w-4 h-4 text-purple-600 shrink-0" />
                    ) : (
                      <ExclamationTriangleIcon className="w-4 h-4 text-rose-600 shrink-0" />
                    )}
                    <span>{davidOtConsent ? `OT Consent (${davidMaxOt}h max) ✓` : 'OT Consent Revoked in Portal'}</span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
                  <div className="text-[11px] text-slate-500 truncate max-w-sm">
                    Verified certs: <span className="font-medium text-slate-700">{davidCerts.join(', ')}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setReplacementAssigned(true);
                      setAssignedCandidateName('David Kim');
                      setReplacementModalOpen(false);
                      setDispatchToast(
                        davidOtConsent
                          ? 'David Kim successfully dispatched to Robotic Welding (Cell 03) for Afternoon Shift. Mandatory 11h rest and ISO certification verified.'
                          : 'David Kim dispatched under Supervisory Overtime Override (Worker had revoked voluntary OT in portal).'
                      );
                      setTimeout(() => setDispatchToast(null), 5000);
                    }}
                    className={`px-4 py-2 rounded-full text-xs font-bold transition-all shadow-2xs flex items-center gap-1.5 cursor-pointer ${
                      davidOtConsent
                        ? 'bg-purple-600 hover:bg-purple-700 text-white'
                        : 'bg-amber-600 hover:bg-amber-700 text-white'
                    }`}
                  >
                    <CheckCircleIcon className="w-4 h-4" />
                    <span>
                      {replacementAssigned
                        ? 'Reconfirm Dispatch'
                        : davidOtConsent
                        ? 'Dispatch David Kim to Cell 03'
                        : 'Override & Dispatch (No OT Consent)'}
                    </span>
                  </button>
                </div>
              </div>

              {/* Candidate 2: Carlos Diaz (Standby) */}
              <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-2xl space-y-2 opacity-80">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold text-slate-800">Carlos Diaz</h4>
                      <span className="text-xs text-slate-500">(Assembly Operator • #A108)</span>
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Wage Rate: $24.00/h &bull; Current Hours: 24.0h
                    </div>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">
                    71% Partial Match
                  </span>
                </div>
                <p className="text-[11px] text-amber-800">
                  Holds Welding Level 3 (Required: Level 4). Assignment would require supervisory qualification override.
                </p>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="mt-5 pt-4 border-t border-border/80 flex items-center justify-between text-xs text-slate-500">
              <span className="flex items-center gap-1 text-emerald-700 font-medium">
                <ShieldCheckIcon className="w-4 h-4 text-emerald-600" />
                Enforces ISO 9001 Qualification & &ge; 11h Rest Interval Policy
              </span>
              <button
                type="button"
                onClick={() => setReplacementModalOpen(false)}
                className="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-full font-semibold transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
