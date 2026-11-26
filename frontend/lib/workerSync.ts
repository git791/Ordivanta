/**
 * Shared Worker Synchronization & Absence Management Store.
 * Bridges Supervisor Dashboard, Recovery Demo, and Worker Portal in real time.
 */

export interface AssignedShift {
  shift_name: string;
  day: string;
  hours: number;
  unit_name: string;
  time: string;
  rest_interval_hours: number;
  is_replacement?: boolean;
}

export interface WorkerProfile {
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
  assigned_shifts: AssignedShift[];
}

export const DEFAULT_WORKERS_DATA: Record<string, WorkerProfile> = {
  emp_david: {
    id: 'emp_david',
    name: 'David Kim',
    role: 'Senior Welding Specialist',
    base_wage: 32.5,
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
    base_wage: 28.0,
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
    base_wage: 31.0,
    skills: ['welding', 'robotic_welding'],
    certifications: ['ISO 9001:2015', 'Welding Level 4'],
    overtime_opt_in: false,
    max_overtime_hours: 4.0,
    is_absent: true,
    absence_reason: 'Medical Leave (Nov 03 - Nov 07)',
    assigned_shifts: [],
  },
};

const SYNC_STORAGE_KEY = 'ordivanta_worker_sync_state';
const SYNC_EVENT_NAME = 'ordivanta-worker-sync';

export function getWorkersSyncState(): Record<string, WorkerProfile> {
  if (typeof window === 'undefined') return DEFAULT_WORKERS_DATA;
  try {
    const raw = localStorage.getItem(SYNC_STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      // Ensure all default workers exist
      return { ...DEFAULT_WORKERS_DATA, ...parsed };
    }
  } catch {
    // ignore
  }
  return DEFAULT_WORKERS_DATA;
}

export function saveWorkersSyncState(state: Record<string, WorkerProfile>): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(SYNC_STORAGE_KEY, JSON.stringify(state));
    window.dispatchEvent(new CustomEvent(SYNC_EVENT_NAME, { detail: state }));
  } catch {
    // ignore
  }
}

/**
 * Report worker absent or return to active duty
 */
export function setWorkerAbsence(
  workerId: string,
  isAbsent: boolean,
  reason: string = 'Medical Leave'
): Record<string, WorkerProfile> {
  const current = getWorkersSyncState();
  const worker = current[workerId] || DEFAULT_WORKERS_DATA[workerId];
  if (!worker) return current;

  const updated: WorkerProfile = {
    ...worker,
    is_absent: isAbsent,
    absence_reason: isAbsent ? reason : undefined,
  };

  // If worker returned to active duty and was Marcus Vance, give back his original shifts
  if (!isAbsent && workerId === 'emp_004') {
    updated.assigned_shifts = [
      { shift_name: 'Afternoon', day: 'Tuesday, Nov 04', hours: 8.0, unit_name: 'Cell 03 (Robotic Welding)', time: '15:00–23:00', rest_interval_hours: 16.0 },
      { shift_name: 'Afternoon', day: 'Wednesday, Nov 05', hours: 8.0, unit_name: 'Cell 03 (Robotic Welding)', time: '15:00–23:00', rest_interval_hours: 16.0 },
    ];
  } else if (isAbsent && workerId === 'emp_004') {
    updated.assigned_shifts = [];
  }

  const newState = {
    ...current,
    [workerId]: updated,
  };

  saveWorkersSyncState(newState);
  return newState;
}

/**
 * Dispatch replacement worker to cover an absent worker's shift
 */
export function dispatchReplacementToWorker(
  workerId: string,
  shift: AssignedShift
): Record<string, WorkerProfile> {
  const current = getWorkersSyncState();
  const worker = current[workerId] || DEFAULT_WORKERS_DATA[workerId];
  if (!worker) return current;

  // Check if replacement shift already exists
  const existing = worker.assigned_shifts.find(
    (s) => s.is_replacement || (s.shift_name === shift.shift_name && s.day === shift.day)
  );

  let newShifts = [...worker.assigned_shifts];
  if (existing) {
    newShifts = newShifts.map((s) => (s === existing ? { ...shift, is_replacement: true } : s));
  } else {
    newShifts.push({ ...shift, is_replacement: true });
  }

  const updated: WorkerProfile = {
    ...worker,
    assigned_shifts: newShifts,
  };

  const newState = {
    ...current,
    [workerId]: updated,
  };

  saveWorkersSyncState(newState);
  return newState;
}

/**
 * Revoke replacement dispatch
 */
export function revokeReplacementFromWorker(workerId: string): Record<string, WorkerProfile> {
  const current = getWorkersSyncState();
  const worker = current[workerId] || DEFAULT_WORKERS_DATA[workerId];
  if (!worker) return current;

  const updated: WorkerProfile = {
    ...worker,
    assigned_shifts: worker.assigned_shifts.filter((s) => !s.is_replacement),
  };

  const newState = {
    ...current,
    [workerId]: updated,
  };

  saveWorkersSyncState(newState);
  return newState;
}

/**
 * Subscribe to worker state changes across tabs / components
 */
export function subscribeWorkersSync(
  callback: (state: Record<string, WorkerProfile>) => void
): () => void {
  if (typeof window === 'undefined') return () => {};

  const handleCustom = (e: Event) => {
    const detail = (e as CustomEvent).detail;
    if (detail) callback(detail);
    else callback(getWorkersSyncState());
  };

  const handleStorage = (e: StorageEvent) => {
    if (e.key === SYNC_STORAGE_KEY) {
      callback(getWorkersSyncState());
    }
  };

  window.addEventListener(SYNC_EVENT_NAME, handleCustom);
  window.addEventListener('storage', handleStorage);

  return () => {
    window.removeEventListener(SYNC_EVENT_NAME, handleCustom);
    window.removeEventListener('storage', handleStorage);
  };
}
