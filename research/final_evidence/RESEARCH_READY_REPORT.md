# ORDIVANTA: RESEARCH-READY FINAL VALIDATION & PROJECT FREEZE REPORT

**Repository:** https://github.com/git791/Ordivanta  
**Review Status:** **RESEARCH READY (PROJECT FROZEN)**  
**Verification Date:** November 17, 2026  

---

## 1. Executive Summary

Ordivanta has completed its rigorous peer-review and scientific audit pass. The system demonstrates a two-module manufacturing workforce optimization architecture backed by published benchmarks, honest computational bounds, and independent post-solve schedule validation.

Every number reported in this evidence package is traced directly to raw JSON and CSV execution logs. **Zero figures or tables contain hardcoded values.**

---

## 2. Core Modules End-to-End Validation

### Module 1: Workforce Shift Planning & Optimization
- **Benchmark Family:** MATSP (`instances1_225`, Côté et al. 2011)
- **Problem Structure:** Discrete 15-minute intervals across 7-to-14 day horizons; continuous shift rotations with multi-station staffing demand.
- **Solvers Compared:** Greedy Constructive Baseline, Two-Stage Lexicographic MILP (HiGHS), ALNS Metaheuristic.
- **Results Summary:** Exact MILP guarantees 100% demand coverage and minimizes workload variance (Std Dev: 1.84h - 3.20h), proving global optimality on instances up to 150 employees (`146_14_150_5`) in 29.18s. ALNS achieves comparable workload balance within 14.77s.

### Module 2: Skill-Based Personnel Task Allocation
- **Benchmark Families:** PTSP (Krishnamoorthy et al. 2012) & SMPTSP (Smet et al. 2014)
- **Problem Structure:** Fixed-time discrete operations on a continuous timeline; multi-skilled personnel pool; strict shift minimisation objective ($\min \sum_w y_w$).
- **Solvers Compared:** Earliest-Start Greedy Heuristic, Exact 0-1 Sparse MILP, ALNS Metaheuristic.
- **Results Summary:** Exact MILP proves true minimal shift counts (e.g. 20 shifts on PTSP `data_2_24_40_33` vs Greedy's 22 shifts). ALNS consistently matches or comes within 1 shift of the optimal bound in sub-0.05s runtime.

### Connected Workflow Bridge & Dynamic Disruption Recovery
- **Bridge Endpoint:** `/api/tasks/workflow/bridge` maps Module 1 shift-rostered personnel directly to Module 2 discrete cell operations.
- **Recovery MILP:** Solves sudden worker absence events (1 to 3 workers) while preserving baseline roster stability, achieving:
  - **1 Worker Absent:** 80.1% ± 8.9% churn reduction vs full rescheduling (2.6 vs 14.6 changed shifts).
  - **2 Workers Absent:** 62.9% ± 13.7% churn reduction vs full rescheduling (5.7 vs 17.5 changed shifts).
  - **3 Workers Absent:** 63.2% ± 7.7% churn reduction vs full rescheduling (8.0 vs 22.4 changed shifts).

---

## 3. Large-Scale Scalability Experiments: 500 & 1,000 Workers

### Formulation Optimization
Replacing naive pairwise interval conflicts ($O(N^2)$) with $O(N \log N)$ **Sweep-Line Interval Maximal Cliques** coupled directly to worker activation ($\sum_{j \in \mathcal{C}_k} x_{wj} \le y_w$) eliminated over 9.7 million redundant constraints:
- **500 workers / 1,200 tasks:** 151,700 binary variables; 51,676 maximal cliques. Built in 12.54s, solved in 47.28s, with only **160.2 MB peak RAM**. Status: `FEASIBLE` (100% complete, 0 errors).
- **1,000 workers / 2,500 tasks:** 628,500 binary variables; 223,203 maximal cliques. Built in 164.70s, solved in 159.46s, with only **891.4 MB peak RAM**. Status: `FEASIBLE` (100% complete, 0 errors).

### Scientific Finding
Exact MILP is mathematically capable of handling 1,000 workers within reasonable RAM limits (<1 GB) and guarantees valid feasible incumbents via warm starts. However, ALNS metaheuristics find significantly tighter rosters (404 shifts vs 449 shifts on 1,000w) in only 10 seconds. In real manufacturing operations, ALNS is the recommended dispatching engine, while MILP serves as the theoretical benchmark.

---

## 4. Evidence Package Index

The `research/final_evidence/` folder contains:
- `dataset_manifest.csv`: Audited metadata across MATSP, PTSP, SMPTSP, and Synthetic extensions.
- `experiment_environment.md`: Hardware, Python, solver versions, and profiling tools.
- `module1_results.csv`: Complete MATSP computational metrics.
- `module2_results.csv`: Full and reduced PTSP & SMPTSP results.
- `scalability_matched_seed101.csv`: Strict matched-instance comparison on Seed 101.
- `scalability_multiseed.csv`: 10-seed multi-run robustness statistics.
- `recovery_results.csv`: Churn reduction and repair metrics under worker absenteeism.
- `validation_summary.md`: Independent post-solve verification rules and results.
- `scenarios/`: Exact JSON scenarios for deterministic Seed 101 runs.
- `solver_logs/`: Complete HiGHS branch-and-cut execution logs across all tiers.
- `figures/`: 10 publication figures at 300+ DPI PNG and vector PDF.
- `screenshots/`: 4 user-interface captures of the live application.
- `reproduction_commands.md`: Step-by-step shell instructions to reproduce all findings.

---

## 5. Freezing Statement

The Ordivanta implementation is hereby **FROZEN** for scientific manuscript preparation. All core research objectives, dataset verifications, algorithmic comparisons, and validation criteria have been fulfilled and empirically documented.
