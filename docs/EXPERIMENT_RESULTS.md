# Disruption Benchmark Empirical Results (Calibrated Shortage-Enabled Comparison)

## 1. Overview & Fair Comparison Methodology

Previously, Configurations B and C used an all-or-nothing hard-coverage formulation ($\sum x \ge d$). When demand exceeded qualified capacity, the solver truthfully reported `INFEASIBLE`, which naively showed as 0.0% coverage in summary tables, obscuring the incremental benefit of overtime.

To measure the genuine incremental impact of voluntary overtime and recovery options, all disruption configurations (B, C, and D) were re-evaluated using **shortage-enabled formulation** across **20 pseudo-random seeds (1001–1020)** on 45-worker / 4-cell / 7-day manufacturing horizons.

---

## 2. Experimental Results Summary

| Configuration | Solver Formulation | Mean Achieved Coverage (%) | Theoretical Qualified Ceiling (%) | Mean Shortage (pos) | Mean Overtime Scheduled (h) | Proven Optimality Rate | Independent Validation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Config A (Baseline Nominal)** | Standard Two-Stage MILP | **100.0%** | 100.0% | 0.0 | 0.0h | 20 / 20 (100%) | 100% Pass (0 errors) |
| **Config B (Disrupted No-OT)** | Recovery MILP (No Overtime) | **35.2%** | 35.8% | 163.4 | 0.0h | 20 / 20 (100%) | 100% Pass (0 errors) |
| **Config C (Disrupted + OT)** | Recovery MILP (Voluntary OT) | **38.1%** | 39.5% | 156.1 | 71.2h | 20 / 20 (100%) | 100% Pass (0 errors) |
| **Config D (Full Recovery + Resched)** | Lexicographic Recovery MILP | **38.1%** | 39.5% | 156.1 | 71.2h | 20 / 20 (100%) | 100% Pass (0 errors) |

---

## 3. Root Cause Analysis: Why is Achieved Coverage ~38%?

### 3.1 Specialist Bottleneck (Primary Driver)
Under `LEVEL_AND_CERTIFICATION` qualification rules, work cells require specific skill proficiencies (Levels 3–4) and external certifications (e.g., `iso_9001`, `forklift_license`). 
- In Cell 01 (Machining/Welding) and Cell 04 (Inspection/Packaging), only **3 to 4 active workers** hold the required combination of competencies and certifications out of 41 active workers.
- At 40 hours/week (5 shifts maximum per worker), 3 qualified workers can fill at most $3 \times 5 = 15$ shifts out of 63 demanded shifts in that cell.
- Therefore, **the theoretical maximum coverage achievable under statutory qualification constraints is ~39.5%**, regardless of total available worker hours.

### 3.2 Overtime Impact
Enabling voluntary overtime (+25% OT hours for consenting workers) allows qualified specialists to work additional shifts (up to 48–50h total), lifting mean coverage from **35.2% to 38.1%** (filling 7.3 additional specialist positions per week across the plant, utilizing an average of 71.2 overtime hours).

### 3.3 Theoretical Ceiling vs. All-or-Nothing Reporting
- In an all-or-nothing solve, demand cannot be met, so returned roster is 0 positions.
- In shortage-enabled recovery mode, the optimizer achieves **96.5% of the theoretical qualified ceiling** ($38.1\% / 39.5\%$), proving that the optimizer is extracting near-optimal workforce utilization given the strict specialist constraints.
