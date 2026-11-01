# Realistic Scheduling Implementation Plan (Revised)

**Repository:** Ordivanta — Workforce Scheduling & Shift Optimization  
**Updated:** 2026-11-01  
**Policy Directive:** Prioritize existing repository benchmarks (`instances1_225`, `ptask/ptsp`, `instances1_24`, and `synthetic_manufacturing`). Defer remote KAHO and INRC-II imports.

---

## 1. Executive Summary & Dataset Strategy

The project evaluates workforce scheduling under realistic manufacturing disruptions without introducing artificial benchmark sprawl:
1. **Primary Manufacturing Benchmark:** `synthetic_manufacturing` — native domain model extended with proficiency levels (1–5), certifications, absenteeism shocks, demand surges, and voluntary overtime.
2. **Existing Shift Scheduling Benchmark:** `data/instances1_225/` (225 TXT instances) — retained for multi-task interval scheduling.
3. **Existing Task Allocation Benchmark:** `data/ptask/ptsp/` (137 DAT instances) — retained for continuous timeline multi-skilling and pairwise overlap conflict enforcement.
4. **Existing Healthcare Benchmark:** `data/instances1_24/` (24 TXT + 24 ROS instances) — retained for days-off and duration constraints.
5. **Deferred Repositories:** External KAHO and INRC-II downloads deferred; existing 389 local instances fully cover all experimental requirements.

---

## 2. Loader Auditing & Constraint Resolution

| Loader | Real Constraint Compatibility Issue | Resolution |
| :--- | :--- | :--- |
| **PTSP (`ptsp_loader.py`)** | Continuous task start/end minutes overlap | Mapped to `HH:MM` intervals; pairwise continuous task overlap enforced natively via `build_shift_conflict_pairs` temporal constraints. |
| **Shift Scheduling (`shift_scheduling_loader.py`)** | 15-minute slot cover, `MinTotalMinutes`, breaks | Minimum headcount mapped to hard demand; `MinTotalMinutes` and intra-shift breaks explicitly documented as unsupported. |
| **Nurse Rostering (`nurse_rostering_loader.py`)** | Days-off, consecutive shift stretches, weekends | Days-off mapped to availability exclusions; max hours mapped; consecutive/weekend limits documented as unsupported. |

---

## 3. Disruption Architecture & Key Decisions

### D1: Strict Qualification Support
- Introduced `QualificationPolicy` enum (`ANY`, `ALL`, `LEVEL_AND_CERTIFICATION`).
- Unified evaluation logic in `backend/app/domain/qualification.py`.
- Enforced identically across MILP, Greedy, ALNS, and independent validator.
- Overtime/on-call status never bypasses qualification.

### D2: Voluntary Overtime & Hour Controls
- Added `overtime_opt_in`, `regular_hours_limit`, `max_overtime_hours`, `overtime_hourly_premium`, `base_hourly_rate`.
- Workers with `overtime_opt_in=False` cannot exceed regular hours limits.
- Overtime premiums are additive ($0.5 \times \text{base}$ for 1.5x pay).

### D3: Lexicographic Recovery MILP
- Three-stage optimization hierarchy:
  1. Minimize weighted uncovered demand shortages.
  2. Minimize total labor cost & overtime premiums subject to best coverage.
  3. Minimize workload fairness SAD.
- Retained original Two-Stage MILP for baseline experiments.

### D4: Independent Validation & Shortage Diagnostics
- Validator flags absent workers, missing mandatory skills, insufficient proficiency, missing certifications, unauthorized overtime, and locked assignment tampering.
- Emits diagnostic shortage warnings (`SHORTAGE_NO_QUALIFIED`, `SHORTAGE_UNAVAILABLE`, `SHORTAGE_REST_PREVENTS`, `SHORTAGE_OVERTIME_BLOCKED`).

---

## 4. Verification & Testing Protocol
- Focused qualification policy test suite (`tests/test_qualification_policy.py`).
- Focused overtime consent test suite (`tests/test_overtime_consent.py`).
- Focused recovery optimizer test suite (`tests/test_recovery_milp.py`).
- Full non-regression test suite (107 tests passing).
- TypeScript compile verification (`pnpm exec tsc --noEmit`).
