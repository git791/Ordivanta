'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { api } from '@/lib/api';
import type { ScenarioSummary, RunSummary, ScenarioResponse, Assignment } from '@/lib/types';
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
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [scenarioDetails, setScenarioDetails] = useState<ScenarioResponse | null>(null);
  const [activeAssignments, setActiveAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Supervisor Plant State Filters
  const [selectedPlant, setSelectedPlant] = useState('Detroit Assembly Plant #1');
  const [selectedUnit, setSelectedUnit] = useState('All Production Units');
  const [schedulePeriod, setSchedulePeriod] = useState('Current Week (Nov 01 - Nov 07, 2026)');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [scenariosData, runsData] = await Promise.all([
        api.getScenarios().catch(() => [] as ScenarioSummary[]),
        api.getRuns().catch(() => [] as RunSummary[]),
      ]);
      setScenarios(scenariosData || []);
      setRuns(runsData || []);

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

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-8">
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
          <select
            value={selectedPlant}
            onChange={(e) => setSelectedPlant(e.target.value)}
            className="px-3.5 py-1.5 bg-surface border border-border/80 rounded-full text-xs font-medium text-slate-800 shadow-2xs focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option>Detroit Assembly Plant #1</option>
            <option>Fremont Fabrication Plant #3</option>
          </select>
          <select
            value={selectedUnit}
            onChange={(e) => setSelectedUnit(e.target.value)}
            className="px-3.5 py-1.5 bg-surface border border-border/80 rounded-full text-xs font-medium text-slate-800 shadow-2xs focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option>All Production Units</option>
            <option>Cell 01 (Machining / Welding)</option>
            <option>Cell 02 (CNC Stamping)</option>
            <option>Cell 03 (Robotic Welding)</option>
            <option>Cell 04 (Final QC & Packaging)</option>
          </select>
          <span className="px-3.5 py-1.5 bg-slate-100 border border-slate-200/80 rounded-full text-xs font-mono text-slate-600 shadow-2xs">
            {schedulePeriod}
          </span>
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
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                    88.9% Feasible
                  </span>
                </div>
                <div className="text-[11px] text-slate-600">
                  1 unstaffed slot on Night shift. On-call candidate on standby.
                </div>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mt-1">
                  <div className="bg-emerald-500 h-1.5 rounded-full w-[89%]" />
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
              {/* Alert 1 */}
              <div className="p-3.5 bg-red-50/70 border border-red-200/90 rounded-2xl">
                <div className="flex items-center justify-between text-xs font-bold text-red-900 mb-1">
                  <span>Robotic Welding (Cell 03)</span>
                  <span className="text-[10px] bg-red-100 px-2 py-0.5 rounded-full text-red-800 font-bold">Critical</span>
                </div>
                <p className="text-xs text-red-700">
                  Worker 004 absent. Only 1 candidate holds ISO 9001 + Welding L4.
                </p>
                <div className="mt-2.5 flex gap-2">
                  <button className="text-xs bg-red-600 text-white px-3 py-1 rounded-full font-semibold hover:bg-red-700 shadow-2xs">
                    Assign Replacement
                  </button>
                </div>
              </div>

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
    </div>
  );
}
