'use client';

import React, { useState, useEffect } from 'react';
import { api, BASE } from '@/lib/api';
import PageHeader from '@/components/ui/PageHeader';
import StatusBadge from '@/components/ui/StatusBadge';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import ErrorBanner from '@/components/ui/ErrorBanner';
import {
  ArrowDownTrayIcon,
  BookOpenIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  LinkIcon,
  BuildingLibraryIcon,
} from '@heroicons/react/24/outline';

export default function DatasetProvenancePage() {
  const [manifest, setManifest] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('shift_scheduling');

  useEffect(() => {
    async function fetchManifest() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getDatasetManifest();
        setManifest(data);
      } catch (err: any) {
        setError(err?.detail || err?.message || 'Failed to fetch dataset manifest');
      } finally {
        setLoading(false);
      }
    }
    fetchManifest();
  }, []);

  const handleDownloadManifest = () => {
    if (!manifest) return;
    const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ordivanta_dataset_manifest.json';
    a.click;
    URL.revokeObjectURL(url);
  };

  const selectedDataset = manifest?.datasets?.find((d: any) => d.id === selectedDatasetId);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-purple-100 text-purple-800">
              Academic Provenance & Standards
            </span>
            <span className="text-xs font-semibold text-slate-500">
              Two-Module Benchmark Alignment
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Dataset Provenance, Limitations & Transformation Registry
          </h1>
          <p className="text-xs text-slate-600 mt-0.5">
            Transparent academic documentation of published benchmark datasets, instances audited, constraint mappings, and research selection rationale.
          </p>
        </div>

        <button
          type="button"
          onClick={handleDownloadManifest}
          disabled={!manifest}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 shadow-2xs transition-all disabled:opacity-50"
        >
          <ArrowDownTrayIcon className="w-4 h-4" />
          <span>Download Machine Manifest (JSON)</span>
        </button>
      </div>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <div className="bg-white border border-border rounded-xl p-8 flex flex-col items-center justify-center gap-3">
          <LoadingSpinner label="Loading dataset manifest and provenance records..." />
          <p className="text-xs text-slate-600">Loading dataset manifest and provenance records...</p>
        </div>
      ) : (
        manifest && (
          <div className="space-y-6">
            {/* Overview Cards: Module Alignment */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gradient-to-br from-indigo-50/50 to-white border border-indigo-200/80 rounded-xl p-4 shadow-2xs">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-indigo-100 text-indigo-800">
                    Module 1 Primary
                  </span>
                  <h3 className="text-sm font-bold text-slate-900">Workforce Shift Planning</h3>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed mb-3">
                  <strong>Selected Dataset:</strong> MATSP Continuous Shift Scheduling Benchmark (225 instances).
                </p>
                <div className="text-[11px] text-slate-700 bg-white/80 p-2.5 rounded-lg border border-indigo-100 space-y-1">
                  <p><strong>Rationale:</strong> Accurately represents multi-activity, multi-day manufacturing shift schedules with 15-minute granular demand requirements and worker capacity bounds.</p>
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-50/50 to-white border border-purple-200/80 rounded-xl p-4 shadow-2xs">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-purple-100 text-purple-800">
                    Module 2 Primary
                  </span>
                  <h3 className="text-sm font-bold text-slate-900">Skill-Based Personnel Task Allocation</h3>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed mb-3">
                  <strong>Selected Datasets:</strong> PTSP (137 instances) and SMPTSP (10 instances, up to 1,577 tasks).
                </p>
                <div className="text-[11px] text-slate-700 bg-white/80 p-2.5 rounded-lg border border-purple-100 space-y-1">
                  <p><strong>Rationale:</strong> Captures discrete workstation operations with exact start/end minutes, multi-skilled qualifications, temporal non-overlap, and shift count minimisation.</p>
                </div>
              </div>
            </div>

            {/* Comprehensive Academic Table */}
            <div className="bg-white border border-border rounded-xl p-4 shadow-2xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Complete Benchmark Dataset Catalog & Metadata
                </h3>
                <span className="text-[11px] text-slate-500">
                  {manifest.datasets?.length ?? 0} Published & Synthetic Suites Audited
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border border-slate-200 rounded-lg">
                  <thead className="bg-slate-50 text-slate-700 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="p-2.5">Dataset Family</th>
                      <th className="p-2.5">Module Alignment</th>
                      <th className="p-2.5">Total Instances</th>
                      <th className="p-2.5">Worker Headcount</th>
                      <th className="p-2.5">Task / Shift Count</th>
                      <th className="p-2.5">Planning Horizon</th>
                      <th className="p-2.5">Citation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-800">
                    {manifest.datasets?.map((d: any) => {
                      const isSelected = d.id === selectedDatasetId;
                      return (
                        <tr
                          key={d.id}
                          onClick={() => setSelectedDatasetId(d.id)}
                          className={`cursor-pointer transition-colors ${
                            isSelected ? 'bg-purple-50/70 font-medium' : 'hover:bg-slate-50/80'
                          }`}
                        >
                          <td className="p-2.5 font-bold text-slate-900">
                            {d.official_name.split('(')[0]}
                            <span className="block text-[10px] font-mono text-slate-500 font-normal">{d.id}</span>
                          </td>
                          <td className="p-2.5">
                            <span className="text-[11px] text-purple-800 font-semibold">{d.module_alignment}</span>
                          </td>
                          <td className="p-2.5 font-bold text-slate-900">{d.total_instances}</td>
                          <td className="p-2.5 font-mono">
                            {d.instance_summary?.min_employees} – {d.instance_summary?.max_employees}
                          </td>
                          <td className="p-2.5 font-mono">
                            {d.instance_summary?.min_tasks} – {d.instance_summary?.max_tasks}
                          </td>
                          <td className="p-2.5 text-slate-600">{d.instance_summary?.horizon_days}</td>
                          <td className="p-2.5 text-slate-500 max-w-xs truncate" title={d.citation}>
                            {d.authors}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Detailed Selected Dataset Dossier */}
            {selectedDataset && (
              <div className="bg-white border border-border rounded-xl p-5 shadow-2xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
                      {selectedDataset.module_alignment}
                    </span>
                    <h2 className="text-base font-bold text-slate-900 mt-1">
                      {selectedDataset.official_name}
                    </h2>
                  </div>
                  {selectedDataset.repository_url?.startsWith('http') && (
                    <a
                      href={selectedDataset.repository_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                    >
                      <LinkIcon className="w-3.5 h-3.5" />
                      <span>Original Repository</span>
                    </a>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="space-y-2 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
                    <h4 className="font-bold text-slate-900 uppercase text-[10px] tracking-wider">Provenance & Metadata</h4>
                    <p><strong>Authors / Creators:</strong> {selectedDataset.authors}</p>
                    <p><strong>Official Citation:</strong> {selectedDataset.citation}</p>
                    <p><strong>Local Directory:</strong> <code className="bg-white px-1.5 py-0.5 rounded border text-[11px]">{selectedDataset.local_path}</code></p>
                    <p><strong>License:</strong> {selectedDataset.license}</p>
                  </div>

                  <div className="space-y-2 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
                    <h4 className="font-bold text-slate-900 uppercase text-[10px] tracking-wider">Constraint Mapping</h4>
                    <div>
                      <span className="font-semibold text-emerald-800">Supported / Mapped Hard Constraints:</span>
                      <ul className="list-disc list-inside mt-1 space-y-0.5 text-slate-700">
                        {selectedDataset.constraints?.supported?.map((c: string, i: number) => (
                          <li key={i}>{c}</li>
                        ))}
                      </ul>
                    </div>
                    {selectedDataset.constraints?.unsupported_or_relaxed?.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-200">
                        <span className="font-semibold text-amber-800">Unsupported or Relaxed Aspects:</span>
                        <ul className="list-disc list-inside mt-1 space-y-0.5 text-slate-600">
                          {selectedDataset.constraints?.unsupported_or_relaxed?.map((c: string, i: number) => (
                            <li key={i}>{c}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )
      )}
    </div>
  );
}
