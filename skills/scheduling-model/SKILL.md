# Skill: Workforce Scheduling Model

## Purpose
Implement, inspect or improve the mathematical scheduling model while preserving hard constraints and truthful solver status.

## Required context
Read `docs/PRD.md`, `docs/TECHNICAL_DESIGN.md` and the current optimisation implementation before editing.

## Procedure
1. Inspect current domain models and reuse them.
2. Validate employee, unit, shift, availability, qualification, demand and hour-limit inputs.
3. Define the binary assignment variable \(x_{ijs}\).
4. Add coverage, availability, qualification, one-assignment-per-shift, maximum-hours and binary-domain constraints.
5. Define an explicit objective that matches available data.
6. Run through the existing solver adapter.
7. Translate the real solver status without guessing.
8. Extract assignments into the canonical domain type.
9. Run the independent schedule validator.
10. Compute metrics from the extracted schedule and input snapshot.
11. Add tests for normal, boundary and infeasible cases.
12. Document assumptions and limitations.

## Hard rules
- Never convert a hard constraint into a penalty without an explicit product decision.
- Never claim optimality unless proven by the solver.
- Never treat missing cost data as zero-cost evidence.
- Never claim overtime or fairness optimisation unless modelled.
- If demand cannot be met, return a truthful infeasible/shortage result.
- The validator must not reuse only the solver's internal constraint state; it should recompute rules from source inputs and assignments.

## Suggested test matrix
- Fully feasible small scenario.
- Demand greater than qualified available workforce.
- Employee unavailable for a requested shift.
- Employee missing unit qualification.
- Duplicate assignment in one shift.
- Total assigned hours above maximum.
- Zero-demand scenario.
- Solver timeout or missing solver.
- Tampered extracted assignment that the independent validator must catch.

## Deliverables
- Model changes.
- Tests.
- Updated objective/constraint documentation.
- Actual test results and known limitations.
