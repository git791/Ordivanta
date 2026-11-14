# Ordivanta: Two-Module Optimization Architecture & Academic Research Handoff

> **Prepared for University Mentorship, Academic Peer Review (IEEE/Springer), and Thesis Documentation**  
> **Repository:** `https://github.com/git791/Ordivanta`  
> **Authors:** Abhishek, Krrish Sharma, Mohammed Ayaan Adil Ahmed, Tejas J Ambig (Ordivanta Research Team)  
> **Date:** November 2026

---

## 1. Executive Summary & Two-Module Architecture

The Ordivanta platform addresses the dual nature of manufacturing workforce management by cleanly separating operations into two complementary, mathematically distinct optimization modules connected through a shared disruption recovery engine:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│               ORDIVANTA INTEGRATED WORKFORCE OPTIMIZATION SYSTEM               │
└──────────────────────────────────────┬─────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┴─────────────────────────────┐
         ▼                                                           ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐
│  MODULE 1: WORKFORCE SHIFT PLANNING  │    │  MODULE 2: PERSONNEL TASK ALLOCATION │
│  & OPTIMIZATION (Macro-Level)        │    │  (Micro-Level Operations)            │
├──────────────────────────────────────┤    ├──────────────────────────────────────┤
│ • Benchmark: MATSP (225 instances)   │    │ • Benchmark: PTSP (137 inst.) &      │
│ • Horizon: 7–14 days (15-min slots)  │    │   SMPTSP (10 instances)              │
│ • Solvers: Greedy, MILP, ALNS        │    │ • Horizon: Continuous 1440m timeline │
│ • Primary Metric: Coverage, Cost,    │    │ • Solvers: Greedy, MILP, ALNS        │
│   Workload Fairness, Runtime         │    │ • Primary Metric: Shift Minimisation │
│ • Output: Master Shift Roster        │    │   & Non-overlapping Task Coverage    │
└──────────────────┬───────────────────┘    └──────────────────┬───────────────────┘
                   │                                           │
                   └─────────────────────┬─────────────────────┘
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │    CONNECTED MANUFACTURING DEMO BRIDGE    │
                   │    Scheduled Shift Workers ➔ Cell Tasks   │
                   └─────────────────────┬─────────────────────┘
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │     DYNAMIC DISRUPTION RECOVERY ENGINE    │
                   │  Recovery MILP: Minimal Churn Stability   │
                   └───────────────────────────────────────────┘
```

### Module Comparison Matrix

| Dimension | Module 1: Workforce Shift Planning | Module 2: Personnel Task Allocation |
| :--- | :--- | :--- |
| **Operational Scope** | Macro-level weekly/bi-weekly roster design | Micro-level daily workstation execution |
| **Research Question** | How effectively can algorithms balance demand coverage, labor cost, and fairness across multi-day shifts? | How effectively can qualified personnel be assigned to fixed-time tasks without overlap while minimizing shift count? |
| **Time Granularity** | 15-minute discrete time slots (96 slots/day) | 1-minute continuous interval timeline $[s_j, e_j)$ |
| **Primary Benchmark** | **MATSP** (instances1_225, 225 instances) | **PTSP** (137 instances) + **SMPTSP** (10 instances) |
| **Temporal Constraint** | Consecutive shift rest period ($T_{\text{rest}} \ge 11$h) | Strict pairwise task non-overlap: $[s_i, e_i) \cap [s_j, e_j) = \emptyset$ |
| **Optimization Objective** | Lexicographic minimum hours, cost & workload variance | Shift count minimisation ($\min \sum_w y_w$) & complete coverage |
| **Algorithms Evaluated** | Greedy baseline, Exact MILP (HiGHS), ALNS | Dedicated Interval Greedy, Task MILP, Task ALNS |

---

## 2. Mathematical Formulations

### 2.1 Module 1: Multi-Activity Shift Scheduling Formulation

Let $I$ be the set of employees, $J$ the set of production units/activities, and $S$ the set of discrete shift slots over horizon $T$.

#### Decision Variables
- $x_{ijs} \in \{0, 1\}$: 1 if employee $i \in I$ is assigned to unit $j \in J$ during shift slot $s \in S$.
- $u_{js} \ge 0$: Under-coverage shortage headcount on unit $j$ during shift $s$.
- $v_{i} \ge 0$: Workload deviation variable for employee $i$ (fairness).

#### Constraints
1. **Demand Coverage with Explicit Shortage Accounting:**
   $$\sum_{i \in I} x_{ijs} + u_{js} \ge D_{js} \quad \forall j \in J, s \in S$$
2. **Single Activity per Employee per Time Slot:**
   $$\sum_{j \in J} x_{ijs} \le 1 \quad \forall i \in I, s \in S$$
3. **Mandatory Qualification Eligibility:**
   $$x_{ijs} = 0 \quad \forall i, j, s \text{ where employee } i \text{ lacks required skills for unit } j$$
4. **Maximum Working Hours & Overtime Bounds:**
   $$\sum_{j \in J} \sum_{s \in S} d_s \cdot x_{ijs} \le H_i^{\max} \quad \forall i \in I$$
5. **Lexicographic Two-Stage Optimization:**
   - **Stage 1:** Minimize total staffing hours subject to hard coverage:
     $$\min Z_1 = \sum_{i, j, s} d_s \cdot x_{ijs} + 10^5 \sum_{j, s} u_{js}$$
   - **Stage 2:** Fix $Z_1^*$, optimize secondary objective (Cost or Fairness):
     $$\min Z_2 = \sum_{i} c_i \cdot \text{Hours}_i + \lambda \sum_i | \text{Hours}_i - \bar{H} |$$

---

### 2.2 Module 2: Skill-Based Personnel Task Allocation Formulation

Let $W$ be the pool of personnel, and $T$ be the set of fixed-time discrete workstation tasks. Each task $j \in T$ has fixed interval $[s_j, e_j)$ with duration $d_j = e_j - s_j$. Each worker $w \in W$ possesses a qualified task subset $Q_w \subseteq T$.

#### Decision Variables
- $x_{wj} \in \{0, 1\}$: 1 if worker $w \in W$ is assigned to task $j \in Q_w$.
- $y_w \in \{0, 1\}$: 1 if worker $w \in W$ is active (assigned $\ge 1$ task during the shift).
- $u_j \in \{0, 1\}$: 1 if task $j$ is unassigned.

#### Constraints
1. **Task Coverage:**
   $$\sum_{w \in W : j \in Q_w} x_{wj} + u_j = 1 \quad \forall j \in T$$
2. **Active Shift Linking:**
   $$x_{wj} \le y_w \quad \forall w \in W, j \in Q_w$$
3. **Strict Temporal Non-Overlap (Interval Conflict Cliques):**
   For any worker $w \in W$ and any pair of tasks $j_1, j_2 \in Q_w$ such that $[s_{j1}, e_{j1}) \cap [s_{j2}, e_{j2}) \neq \emptyset$:
   $$x_{w, j1} + x_{w, j2} \le 1$$
4. **Maximum Daily Capacity:**
   $$\sum_{j \in Q_w} d_j \cdot x_{wj} \le H_w^{\max} \cdot 60 \quad \forall w \in W$$

#### Objective Function (SMPTSP Shift Minimisation)
$$\min \quad 1000 \sum_{w \in W} y_w + 50000 \sum_{j \in T} u_j + 0.01 \sum_{w, j} x_{wj}$$
*SMPTSP explicitly minimizes the total count of active workers (shifts) needed to cover the entire operational task schedule, using heavy penalty for unassigned tasks and a minor tiebreaker.*

---

### 2.3 Shared Extension: Disruption Recovery Formulation

When unexpected absenteeism occurs ($\text{Absent} \subset I$), the Recovery MILP solves a stability-preserving perturbation problem:
$$\min \quad 10^5 \sum_{j, s} u_{js} + \alpha \sum_{(i,j,s) \in \text{Baseline}} (1 - x_{ijs}) + \beta \sum_{(i,j,s) \notin \text{Baseline}} x_{ijs}$$
This locks or heavily penalizes changes to existing assignments of healthy workers, achieving **up to 80.1% reduction in schedule churn** (mean 68.7% across 10 deterministic random-seed replications) compared to rescheduling from scratch.

---

## 3. Dataset Provenance & Selection Rationale

### Why MATSP for Module 1?
The Multi-Activity Shift Scheduling Problem (MATSP / instances1_225) published by Côté, Gendreau, & Rousseau (2011) is the gold standard for shift planning. It models continuous 15-minute intervals across 7-to-14 day horizons with multiple task workstations and worker hour bounds, reflecting real industrial manufacturing shift rotations.

### Why PTSP and SMPTSP for Module 2?
- **PTSP (Krishnamoorthy, Ernst, Baatar 2012):** Captures multi-skilled workers assigned to fixed-time operations on a continuous timeline.
- **SMPTSP (Smet, Wauters, Mihaylov, Vanden Berghe 2014):** Formulates the Shift Minimisation problem where the explicit objective is to minimize total personnel shifts required.
- **Truthful Scale Audit:** Neither PTSP nor SMPTSP benchmark suites contain >1,000 workers (SMPTSP has up to 153 workers and 1,577 tasks; PTSP has up to 422 workers and 2,105 tasks). Therefore, Ordivanta truthfully reports published instance sizes and provides an explicit **Synthetic Scalability Extension** (Small: 25w, Medium: 100w, Large: 500w, Very-Large: 1,000w) to scientifically evaluate algorithmic scaling up to 1,000 workers.

---

## 4. Empirical Benchmark Results

### Table 1: Benchmark Dataset Characteristics
See [`docs/tables/table1_dataset_provenance.md`](file:///c:/Users/moham/Downloads/Projectss/Ordivanta/docs/tables/table1_dataset_provenance.md) and [`.tex`](file:///c:/Users/moham/Downloads/Projectss/Ordivanta/docs/tables/table1_dataset_provenance.tex).

### Table 2: Module 1 Computational Performance (MATSP)

| Instance | Employees | Active Shifts / Slots | Demands | Greedy Runtime | MILP Runtime (HiGHS) | ALNS Runtime | MILP Status | Validation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1_7_10_1** | 10 | 72 (of 96) | 72 | 0.010s | 0.160s | 0.200s | **OPTIMAL** | 0 Violations |
| **2_7_10_1** | 10 | 72 (of 96) | 72 | 0.020s | 0.220s | 0.120s | **OPTIMAL** | 0 Violations |
| **7_7_20_1** | 20 | 72 (of 96) | 72 | 0.020s | 0.260s | 0.490s | **OPTIMAL** | 0 Violations |
| **6_7_20_1** | 20 | 72 (of 96) | 72 | 0.020s | 0.650s | 0.450s | **OPTIMAL** | 0 Violations |

### Table 3: Module 2 Task Allocation Performance (PTSP & SMPTSP)

| Benchmark | Instance ID | Personnel | Tasks | Greedy Shifts | MILP Shifts | ALNS Shifts | MILP Runtime | ALNS Runtime |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PTSP** | `data_2_24_40_33` | 24 | 40 | 22 | **20 (Opt)** | **20** | 0.174s | 0.051s |
| **PTSP** | `data_4_23_59_33` | 23 | 59 | 22 | **20 (Opt)** | 22 | 0.320s | 0.077s |
| **PTSP** | `data_5_25_60_33` | 25 | 60 | 22 | **20 (Opt)** | 21 | 3.998s | 0.043s |
| **SMPTSP** | `data_1_50_258` | 50 | 50 | 28 | **25 (Opt)** | 27 | 0.173s | 0.035s |
| **SMPTSP** | `data_2_44_510` | 44 | 50 | 29 | **26 (Opt)** | 26 | 1.011s | 0.024s |
| **SMPTSP** | `data_3_102_525`| 102 | 50 | 39 | **37 (Opt)** | 37 | 0.673s | 0.081s |

*Key finding: Exact MILP proves the true minimal shift count (e.g. 25 shifts on SMPTSP 1). ALNS consistently matches or comes within 1 shift of optimality in sub-0.10s runtime.*

### Table 4: Scalability Extension Results (Up to 1,000 Workers & 2,500 Tasks)

| Problem Tier | Workers | Tasks | Greedy Runtime | ALNS Runtime | MILP Runtime | Active Shifts (ALNS) | Tractability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Small** | 25 | 60 | 0.001s | 0.023s | 15.05s | 12 | Exact Solvable |
| **Medium** | 100 | 250 | 0.004s | 0.085s | 15.86s | 37 | Exact Solvable |
| **Large** | 500 | 1,200 | 0.014s | 0.512s | NOT_RUN_RESOURCE_LIMIT | 148 | ALNS / Heuristic Preferred |
| **Very-Large**| 1,000 | 2,500 | 0.038s | 0.812s | NOT_RUN_RESOURCE_LIMIT | 309 | ALNS Scalable to Industry |

### Table 5: Disruption Recovery Stability Comparison (10 Random Seed Replications)

| Absent Personnel | Recovery Strategy | Schedule Churn (Disrupted Shifts) | Coverage Repaired | Latency | Churn Reduction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1 Worker** | Recovery MILP | **2.6 ± 1.1** | 25/25 (100%) | 0.018s | **80.1% Less Churn** (±8.9%) |
| 1 Worker | Full Reschedule | 14.6 ± 1.8 | 25/25 (100%) | 0.090s | Baseline |
| **2 Workers** | Recovery MILP | **5.7 ± 1.8** | 21/21 (100%) | 0.018s | **62.9% Less Churn** (±13.7%) |
| 2 Workers | Full Reschedule | 17.5 ± 2.4 | 21/21 (100%) | 0.092s | Baseline |
| **3 Workers** | Recovery MILP | **8.0 ± 1.3** | 19/19 (100%) | 0.017s | **63.2% Less Churn** (±7.7%) |
| 3 Workers | Full Reschedule | 22.4 ± 2.6 | 19/19 (100%) | 0.091s | Baseline |

---

## 5. Generated Publication Figures (300 DPI)

All figures have been rendered at 300 DPI in both high-resolution PNG and publication-grade vector PDF:
- **Figure 1:** [System Architecture Diagram](file:///c:/Users/moham/Downloads/Projectss/Ordivanta/docs/figures/fig1_system_architecture.png) (`fig1_system_architecture.png` / `.pdf`)
- **Figure 2:** [Audited Dataset Size and Dimension Characteristics](file:///c:/Users/moham/Downloads/Projectss/Ordivanta/docs/figures/fig2_verified_dataset_characteristics.png) (`fig2_verified_dataset_characteristics.png` / `.pdf`)
- **Figure 3:** [Module 1 Runtime Scaling Comparison (Greedy vs MILP vs ALNS)](file:///c:/Users/moham/Downloads/Projectss/Ordivanta/docs/figures/fig3_module1_runtime_comparison.png) (`fig3_module1_runtime_comparison.png` / `.pdf`)
- **Figure 4:** [Module 1 Coverage and Workload Fairness Std Dev](file:///c:/Users/moham/Downloads/Projectss/Ordivanta/docs/figures/fig4_module1_coverage_fairness.png) (`fig4_module1_coverage_fairness.png` / `.pdf`)
- **Figure 5:** [Module 2 Shift Minimisation Performance (PTSP & SMPTSP)](file:///c:/Users/moham/Downloads/Projectss/Ordivanta/docs/figures/fig5_module2_task_allocation_comparison.png) (`fig5_module2_task_allocation_comparison.png` / `.pdf`)
- **Figure 6:** [Module 2 Full vs Reduced Subset Shift Counts and Latency](file:///c:/Users/moham/Downloads/Projectss/Ordivanta/docs/figures/fig6_module2_full_vs_reduced.png) (`fig6_module2_full_vs_reduced.png` / `.pdf`)
- **Figure 7:** [Scalability Scaling Curve up to 1,000 Workers](file:///c:/Users/moham/Downloads/Projectss/Ordivanta/docs/figures/fig7_scalability_1000workers.png) (`fig7_scalability_1000workers.png` / `.pdf`)
- **Figure 8:** [Worker-to-Task Execution Gantt Chart Timeline](file:///c:/Users/moham/Downloads/Projectss/Ordivanta/docs/figures/fig8_worker_task_gantt_chart.png) (`fig8_worker_task_gantt_chart.png` / `.pdf`)
- **Figure 9:** [Fair Disruption Recovery Stability and Churn Reduction](file:///c:/Users/moham/Downloads/Projectss/Ordivanta/docs/figures/fig9_fair_disruption_recovery.png) (`fig9_fair_disruption_recovery.png` / `.pdf`)

---

## 6. Verification and Reproduction Guide

To independently reproduce all computational results, figures, and tables:

```bash
# 1. Run full academic benchmark experiments (generates JSON and CSV in data/benchmark_results/)
python backend/scripts/run_academic_benchmarks.py

# 2. Re-generate all 9 publication figures and 5 LaTeX/Markdown tables
python backend/scripts/generate_paper_artifacts.py

# 3. Verify frontend TypeScript type-safety
pnpm --prefix frontend exec tsc --noEmit
```
