# Mentor Presentation Notes: Dataset Realism & Workforce Recovery

This document provides a concise overview of the problem, implementation, empirical findings, and limitations for academic review and stakeholder presentation.

---

## 1. Problem Statement & Research Motivation

Prior versions of Ordivanta exhibited two key limitations common in scheduling literature:
1. **Synthetic Instance Bias:** Schedules assumed 100% attendance, static demand, and lack of voluntary overtime boundaries.
2. **Disjunctive Qualification Weakness:** The system permitted assignment if an employee possessed *any one* matching skill, ignoring mandatory multi-skill roles, proficiency tiers, and statutory certifications.

---

## 2. Implemented Capabilities vs. Baseline

| Feature | Baseline Implementation | Extended Implementation |
| :--- | :--- | :--- |
| **Qualification Policy** | Disjunctive (`ANY`) only | Configurable `ANY`, `ALL`, and `LEVEL_AND_CERTIFICATION` across all optimizers and validator. |
| **Workforce Realism** | Full attendance assumed | Configurable absenteeism (`is_absent` flag), voluntary overtime opt-in consent, regular vs OT hour caps. |
| **Demand Variations** | Static demand fixtures | Unit-shift demand shocks (e.g. +20% surge) with integer ceiling rounding policies. |
| **Solver Formulations** | Hard-constraint Two-Stage MILP | Retained baseline MILP + Added Three-Stage Lexicographic Recovery MILP with explicit shortage variables. |
| **Independent Validator** | Basic availability & skills | Added checks for absent employee assignments, unauthorized overtime, OT caps, missing certs, and shortage diagnostics. |

---

## 3. Key Empirical Findings (20 Pseudo-Random Seeds)

From `docs/EXPERIMENT_RESULTS.md`:
- **Baseline (Config A):** 100% coverage achieved with proven global mathematical optimality (`OPTIMAL` status in 20/20 runs).
- **Disrupted Shock (Config B - 10% absent, +20% demand, strict qualification):** Truthfully proven `INFEASIBLE` in 20/20 runs. The solver never relaxed hard constraints or falsified feasibility.
- **Voluntary Overtime (Config C):** Capacity was expanded for consenting employees, but specialist certification bottlenecks still proved infeasible.
- **Recovery MILP (Config D):** Successfully generated valid, actionable recovery rosters with an average of 37.6% coverage under extreme overload, strictly prioritizing critical cell demand while maintaining 100% independent validation compliance.

---

## 4. Benchmark Provenance & Authenticity
- Curtois & Qu (2014) *instances1_24* raw files are preserved in `data/instances1_24/instances1_24/`.
- Unmapped constraints (such as consecutive shift limits and minimum rest blocks) are explicitly recorded as unsupported rather than fabricated.
- No synthetic certifications or wage levels are attributed to public benchmark datasets.

---

## 5. Unresolved Limitations & Future Roadmap
1. **Heuristic Shortage Diagnostics:** Shortage explanations identify probable causes based on employee attributes, but are not formal mathematical infeasibility certificates (such as Farkas dual rays).
2. **Dynamic Task Overlap in PTSP:** Continuous task preemption remains outside the discrete shift formulation.
3. **Multi-Horizon Rolling Rescheduling:** Real-time re-optimisation upon shift handover requires persistent state management planned for Phase 2 releases.
