# Disruption Experiment Protocol

## 1. Experimental Objectives
Empirically evaluate and compare workforce scheduling mechanisms across baseline and disruption conditions:
1. **Configuration A (Original Baseline):** Nominal demand, 0% absenteeism, no overtime, disjunctive (`ANY`) qualification.
2. **Configuration B (Disrupted Baseline):** 10% absenteeism, +20% demand surge, strict (`LEVEL_AND_CERTIFICATION`) qualifications, no overtime.
3. **Configuration C (Overtime Enabled):** 10% absenteeism, +20% demand, strict qualifications, approved voluntary overtime enabled.
4. **Configuration D (Full Recovery):** 10% absenteeism, +20% demand, strict qualifications, approved overtime, on-call options, and recovery optimization.

---

## 2. Experimental Parameters & Seeds
- **Instance Size:** 20 employees, 4 production cells, 7-day planning horizon (21 shifts).
- **Repetitions / Seeds:** 20 distinct random seeds (Seeds `1001` through `1020`).
- **Algorithms Evaluated:**
  - Standard Two-Stage MILP (`milp_scheduler.py`)
  - Recovery MILP (`recovery_milp_scheduler.py`)
  - Greedy Baseline (`greedy_scheduler.py`)
  - ALNS Metaheuristic (`alns_scheduler.py`)
- **Rest Interval:** 11-hour minimum rest between consecutive shifts.

---

## 3. Metrics Collected
For each run, the following metrics are recorded:
- **Coverage Rate (%):** Staffed positions / demanded positions.
- **Unfilled Positions:** Total staffing headcount shortages.
- **Total Labor Cost ($):** Base wages + overtime premiums.
- **Overtime Hours:** Hours scheduled in excess of regular hours limits.
- **Workload SAD (h):** Sum of absolute deviations from target hours.
- **Workload Std Dev (h):** Standard deviation of scheduled hours across workers.
- **Solver Status:** Exact status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `NOT_SOLVED`, `ERROR`).
- **Runtime (s):** Wall-clock solver execution time.
- **Independent Validation:** Binary pass/fail and violation count.
