# Ordivanta: Complete End-to-End System Walkthrough & Technical Guide

> **A Comprehensive Step-by-Step Guide to the Architecture, Mathematical Optimization Engines, Benchmark Datasets, Frontend Workflows, and Academic Defensibility of Ordivanta.**

---

## 1. Executive Overview & System Philosophy

### What is Ordivanta?
**Ordivanta** is an industrial-grade workforce scheduling and task allocation platform built specifically for manufacturing operations. It replaces error-prone spreadsheets with **rigorous operations research (OR)** algorithms that mathematically optimize employee schedules while strictly enforcing qualification policies, capacity limits, and shop-floor temporal non-overlap constraints.

### The Core Problem in Manufacturing Plants
Modern manufacturing plants face two conflicting challenges at different time scales:
1. **The Macro Problem (Shift Planning):** Weeks in advance, the plant manager must build a weekly or bi-weekly shift roster across 3 shifts (Morning, Afternoon, Night) ensuring every cell has adequate headcount while controlling overtime and fatigue.
2. **The Micro Problem (Workstation Task Allocation):** During each operational day, dozens of discrete, fixed-time operations (e.g. 45-minute robotic welding runs, 30-minute stamping die adjustments, 15-minute ultrasound weld inspections) must be assigned to qualified technicians. No technician can be double-booked across overlapping intervals, and the plant must minimize the total headcount (shifts) brought into the building.

Spreadsheets fail completely at this because checking millions of combinations of certifications and minute-level temporal conflicts is humanly impossible.

---

## 2. The Two-Module Optimization Architecture

To cleanly model this reality, Ordivanta is architected into **two mathematically distinct optimization modules** connected by a shared disruption recovery engine:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│               ORDIVANTA INTEGRATED WORKFORCE OPTIMIZATION SYSTEM               │
└──────────────────────────────────────┬─────────────────────────────────────────┘
                                       │
         ┌─────────────────────────────┴─────────────────────────────┐
         ▼                                                           ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐
│  MODULE 1: WORKFORCE SHIFT PLANNING  │    │  MODULE 2: PERSONNEL TASK ALLOCATION │
│  (Macro-Level Roster Design)         │    │  (Micro-Level Workstation Schedule)  │
├──────────────────────────────────────┤    ├──────────────────────────────────────┤
│ • Benchmark: MATSP (225 instances)   │    │ • Benchmarks: PTSP (137 instances) & │
│ • Granularity: 15-min discrete slots │    │   SMPTSP (10 instances)              │
│ • Horizon: 7 to 14 days              │    │ • Granularity: 1-min continuous time │
│ • Constraints: Max hours, rest spans │    │ • Constraints: Strict non-overlap,   │
│ • Primary Metric: Coverage, Cost &   │    │   multi-skilling certification matrix│
│   Workload Variance Fairness         │    │ • Primary Metric: Shift Minimisation │
│ • Solvers: Greedy, MILP, ALNS        │    │ • Solvers: Interval Greedy, MILP,    │
│ • Output: Master Shift Roster        │    │   ALNS Metaheuristic                 │
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

---

## 3. Module 1: Workforce Shift Planning & Optimization (Macro-Level)

### 3.1 Purpose & Scope
Module 1 creates the **Master Shift Roster**. Given customer production volume, the factory determines how many workers are needed at each workstation cell (Machining, Stamping, Robotics, QC) across morning, afternoon, and night shifts.

### 3.2 Primary Benchmark: MATSP (225 Instances)
- **Source:** Côté, Gendreau, & Rousseau (2011), *INFORMS Journal on Computing*.
- **Dataset Location:** `data/instances1_225/instances1_225/txt/`
- **Characteristics:** Continuous multi-activity shift scheduling across 7–14 days with 15-minute intervals (96 slots/day) and individual employee maximum working minute caps.

### 3.3 The Three Solvers in Module 1
1. **Greedy Baseline (`greedy_scheduler.py`):**
   - Sorts shifts chronologically and assigns available qualified workers with the lowest cumulative hours.
   - Serves as the benchmark reference representing standard heuristic rostering.
2. **Two-Stage Lexicographic MILP (`milp_scheduler.py`):**
   - **Stage 1:** Solves an exact Mixed-Integer Linear Program to minimize total scheduled labor hours subject to hard coverage constraints.
   - **Stage 2:** Fixes the proven optimal labor hours $Z_1^*$ and optimizes secondary objectives:
     - **Cost Mode:** Minimizes weighted wage expense $\sum c_i \cdot \text{Hours}_i$.
     - **Fairness Mode:** Minimizes the deviation of each worker’s scheduled hours from the plant mean $\sum | \text{Hours}_i - \bar{H} |$.
3. **Adaptive Large Neighborhood Search (`alns_scheduler.py`):**
   - Rapid metaheuristic using Destroy operators (random shift unassignment, worker duty wipe) and Repair operators (regret-based insertion).
   - Designed to deliver 95%+ optimal rosters in milliseconds.

---

## 4. Module 2: Skill-Based Personnel Task Allocation (Micro-Level)

### 4.1 Purpose & Scope
Module 2 solves the **Shop-Floor Execution Problem**. When workers arrive at the plant for an 8-hour shift, they must be assigned to specific, fixed-time machine tasks throughout the day without schedule overlap.

### 4.2 Primary Benchmarks: PTSP & SMPTSP
- **PTSP (Personnel Task Scheduling Problem):** 137 instances from Krishnamoorthy, Ernst, & Baatar (2012). Models continuous task intervals $[s_j, e_j)$ and multi-skilling qualification lists.
- **SMPTSP (Shift Minimisation Personnel Task Scheduling Problem):** 10 instances from Smet, Wauters, Mihaylov, & Vanden Berghe (2014) in `data/smptsp/instances/`. Evaluates assigning tasks while **minimizing total shifts/workers utilized**.

### 4.3 The Mathematical Formulation (`task_milp_solver.py`)
Module 2 is a dedicated interval optimization formulation:

1. **Decision Variables:**
   - $x_{w,j} \in \{0, 1\}$: Worker $w$ is assigned to task $j$.
   - $y_w \in \{0, 1\}$: Worker $w$ is active (called into the factory).
   - $u_j \in \{0, 1\}$: Task $j$ is unassigned (penalty variable).

2. **Temporal Non-Overlap Conflict Cliques:**
   For any worker $w$ and any pair of tasks $j_1, j_2$ whose continuous execution intervals overlap ($[s_{j1}, e_{j1}) \cap [s_{j2}, e_{j2}) \neq \emptyset$):
   $$x_{w, j_1} + x_{w, j_2} \le 1$$
   *This guarantees that a worker can never be scheduled in two places at the same time.*

3. **Active Shift Linking:**
   $$x_{w, j} \le y_w \quad \forall j \in Q_w$$
   *Forces $y_w = 1$ if worker $w$ performs at least one task during the day.*

4. **SMPTSP Objective Function:**
   $$\min \quad 1000 \sum_{w \in W} y_w + 50000 \sum_{j \in T} u_j + 0.01 \sum_{w, j} x_{w, j}$$
   *Tells the HiGHS C++ solver to find the absolute minimum headcount $\sum y_w$ needed to achieve 100% task coverage.*

### 4.4 The 3 Solvers in Module 2
- **Exact MILP (`task_milp_solver.py`):** Formulates the 0–1 integer program in PuLP and solves it via HiGHS branch-and-bound. Proves global mathematical optimality (e.g., exactly 24 workers needed).
- **ALNS Metaheuristic (`task_alns_solver.py`):** Uses candidate-sampled Regret-2 insertion and Simulated Annealing. Converges in ~0.02s (5x faster than MILP) and consistently matches or comes within 1 shift of the optimal minimum.
- **Greedy Baseline (`task_greedy_solver.py`):** Packs tasks by earliest start time into already-active qualified workers. Fast (0.0007s), but leaves suboptimality (calls in 27 workers instead of 24).

---

## 5. The Connected Manufacturing Workflow & Disruption Engine

### 5.1 The Connected Demonstration Bridge
In real manufacturing, macro shift planning feeds micro task allocation. Ordivanta implements an explicit demonstration bridge (`POST /api/tasks/workflow/bridge`):
1. **Module 1 Output:** Produces 8 active, scheduled operators for Detroit Assembly Plant #1 Day Shift (07:00–15:30).
2. **Workstation Translation:** Deconstructs the shift into 12 fine-grained workstation tasks across 4 shop-floor production cells:
   - Cell 01: Sub-assembly Chassis Weld Prep, Heavy Bracket TIG Finishing
   - Cell 02: High-Precision CNC Stamping Feed, Die Maintenance
   - Cell 03: Structural Robotic MIG Welding Run A & B, Recalibration
   - Cell 04: Ultrasound Integrity Inspection, CMM Laser Scan, Packaging
3. **Module 2 Solve:** MILP assigns the 8 operators to the 12 tasks, proving 100% coverage with 0 temporal overlap.

### 5.2 Dynamic Disruption Recovery (`recovery_milp_scheduler.py`)
When a scheduled operator calls in sick:
- **Rescheduling from Scratch is Catastrophic:** In a real factory, re-solving from scratch disrupts everyone's shifts (high churn), creating chaos on the floor.
- **Ordivanta Recovery MILP:** Solves a stability-preserving perturbation problem:
   $$\min \quad 10^5 \sum u_{js} + \alpha \sum_{(i,j,s) \in \text{Baseline}} (1 - x_{ijs}) + \beta \sum_{(i,j,s) \notin \text{Baseline}} x_{ijs}$$
- **Result:** Keeps healthy workers in their original assignments, repairing 100% of coverage in **0.018 seconds** with **up to 80.1% less churn** (mean 68.7% across 10 random seeds) than full rescheduling.

---

## 6. Frontend Guide: Page-by-Page & Button-by-Button

| URL / Page | Name & Role | Key Controls & How to Use |
| :--- | :--- | :--- |
| **`/schedule`** | **Shift Planner (Module 1)** | • Select shift scenario.<br>• Choose objective: *Cost Minimisation*, *Workload Fairness*, or *Strict Feasibility*.<br>• Click **"Optimize Roster (MILP)"** to generate the calendar roster, coverage heatmaps, and worker breakdown. |
| **`/tasks`** | **Task Allocation (Module 2)** | • **Benchmark Switcher:** Choose **SMPTSP** (Shift Minimisation) or **PTSP** (OR-Library).<br>• **Instance Dropdown:** Choose test instances (e.g., `data_1_50_258` with 45 tasks, 50 workers).<br>• **"Compare All 3 Algorithms":** Renders the 3-Way Hero Comparison Deck (Exact MILP vs ALNS vs Greedy), graphical tradeoff bars, and detailed comparison matrix.<br>• **"Connected Roster Demo":** Demonstrates Module 1 feeding into Module 2 manufacturing cells.<br>• **Schedule Switcher:** Toggle between MILP, ALNS, and Greedy minute-by-minute timeline schedules. |
| **`/provenance`** | **Dataset Provenance** | • Displays the complete academic metadata table for all 5 dataset families.<br>• Mentor selection rationales.<br>• Click **"Download Machine Manifest (JSON)"** to get `dataset_manifest.json`. |
| **`/experiments`** | **Batch Benchmark Lab** | • Load published MATSP shift benchmark instances.<br>• Compare solver runtimes and objective scores side-by-side. |
| **`/demo`** | **Plant Digital Twin** | • Interactive plant floor showing live cell bottleneck telemetry for Cell 01 to Cell 04. |
| **`/worker`** | **Worker Self-Service** | • Personal portal showing assigned shifts, skill proficiency levels, and overtime availability. |

---

## 7. Reproduction & Verification Commands

All benchmark data, figures, and tables can be independently reproduced at any time:

```powershell
# 1. Run all academic benchmark experiments (generates JSON & CSV in data/benchmark_results/)
backend\.venv\Scripts\python.exe backend\scripts\run_academic_benchmarks.py

# 2. Re-generate all 9 publication figures (300 DPI PNG & vector PDF) and 5 LaTeX/MD tables
python backend\scripts\generate_paper_artifacts.py

# 3. Verify frontend TypeScript type-safety
pnpm --prefix frontend exec tsc --noEmit
```

---

## 8. Academic Defense & Mentor Presentation Script

When presenting Ordivanta to your mentor or thesis committee, use this structured explanation:

1. **Why two modules?**  
   *"Manufacturing operations inherently operate on two different mathematical timescales: macro-level shift planning across days (Module 1, modeled via MATSP), and micro-level workstation task scheduling across continuous minutes (Module 2, modeled via PTSP and SMPTSP). Modeling them as separate but connected modules reflects genuine industrial practice."*

2. **Why evaluate three algorithms?**  
   *"Exact MILP provides the mathematical benchmark of proven optimality, showing the theoretical minimum headcount (e.g., 24 workers). Greedy demonstrates the operational penalty of naive heuristics (+3 extra shifts, +11.1% payroll waste). ALNS metaheuristic demonstrates industrial scalability, solving instances up to 1,000 workers and 2,500 tasks in seconds while capturing 96%+ of the optimal headcount savings."*

3. **How do you guarantee real-world safety?**  
   *"Every schedule generated by every solver is independently audited by a post-solve validator using the raw input timestamps. An assignment is accepted only if it satisfies 100% of hard qualifications, working hours, and interval non-overlap constraints."*
