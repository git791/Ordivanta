# Product Requirements Document (PRD)
## Ordivanta — Workforce Scheduling & Shift Optimization

**Status:** Proposed MVP specification  
**Product type:** Web-based decision-support application  
**Primary users:** Manufacturing planner, shift supervisor, operations manager  
**Algorithm strategy:** MILP primary; Greedy baseline  
**Frontend:** Next.js / React / TypeScript (not Streamlit)

## 1. Executive summary

Ordivanta helps manufacturing planners create, inspect and compare employee rosters for production units and shifts. It transforms staffing demand and workforce constraints into a structured optimisation problem, generates a candidate schedule, validates that schedule independently and presents the result in an operational dashboard.

The MVP is successful when a user can supply a valid scenario, run a scheduler, understand its status and inspect an independently validated roster without relying on manual interpretation of solver internals.

## 2. Problem statement

Manual scheduling can overlook worker availability, qualification requirements, duplicate shift assignments, working-hour limits or unit-level staffing demand. Ordivanta provides a repeatable model and validation process to reduce these avoidable errors and make schedule quality measurable.

## 3. Goals

1. Model employee-to-unit-to-shift assignments explicitly.
2. Satisfy configured hard constraints in every accepted schedule.
3. Surface infeasibility and incomplete coverage clearly.
4. Provide a baseline scheduler for a fair comparison with MILP.
5. Measure schedule quality with transparent metrics.
6. Make the workflow understandable to a supervisor who is not an optimisation specialist.

### Non-goals for the first release
- Automated payroll, HRIS or ERP integration.
- Machine sequencing or full production planning.
- Predictive demand forecasting.
- Mobile employee self-service.
- Guaranteed global optimality when the solver has not proved optimality.
- Automatic enforcement of legal rules not explicitly configured and verified.
- Advanced fatigue, preferences or multi-objective Pareto optimisation unless separately scoped.

## 4. Personas

### Planner / Supervisor
Needs to define demand, check workforce availability, generate a roster and identify shortages before approving it.

### Operations Manager
Needs a concise view of coverage, workload distribution, cost metrics when available, solver status and differences between algorithms.

### Project Evaluator / Developer
Needs reproducible scenarios, documented assumptions, testable constraints and results that can be explained during a demonstration.

## 5. Core user stories and acceptance criteria

### US-01: Manage scheduling inputs
As a planner, I can enter employees, qualifications, availability, shift durations, units and required headcount.

**Acceptance**
- Required fields are validated.
- Unknown employee/unit/shift references are rejected.
- Invalid or duplicate identifiers are surfaced before solving.
- Sample data can be loaded for a repeatable demonstration.

### US-02: Validate a scenario
As a planner, I can check the input before running an optimiser.

**Acceptance**
- Validation reports errors and warnings separately.
- Invalid scenarios cannot be sent to the solver.
- Messages identify the relevant entity and the corrective action where possible.

### US-03: Generate a MILP schedule
As a planner, I can request a schedule using the MILP model.

**Acceptance**
- Model contains documented assignment variables and configured hard constraints.
- Solver status and runtime are recorded.
- The UI does not label a feasible-but-unproven result as optimal.
- Infeasible or failed runs do not masquerade as valid completed schedules.

### US-04: Compare a Greedy baseline
As an evaluator, I can run a Greedy baseline against the same scenario.

**Acceptance**
- Both algorithms receive the same normalized input.
- Both outputs pass through the same independent validator.
- Metrics and runtime are presented side by side.
- The comparison reports limitations and does not assume MILP always wins on runtime.

### US-05: Inspect a schedule
As a supervisor, I can filter assignments by shift, production unit and employee.

**Acceptance**
- Each assignment identifies employee, unit, shift and scheduled hours.
- Coverage is shown per unit and shift.
- Missing coverage and validation violations are clearly listed.
- Status is communicated through text and icon/shape in addition to colour.

### US-06: Export results
As a planner, I can export a schedule for review.

**Acceptance**
- CSV includes scenario/run identifiers, employee, unit, shift and hours.
- Export includes status metadata or a companion summary.
- Only a validated roster is exported as an approved candidate; incomplete results must be explicitly marked.

## 6. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Create/load employees and their skills | Must |
| FR-02 | Define employee availability and hour limits | Must |
| FR-03 | Define production units and shift-level demand | Must |
| FR-04 | Validate scenario inputs | Must |
| FR-05 | Build and solve MILP model | Must |
| FR-06 | Run Greedy baseline | Should |
| FR-07 | Independently validate assignments | Must |
| FR-08 | Display solver status and coverage | Must |
| FR-09 | Show workload and runtime metrics | Must |
| FR-10 | Export roster to CSV | Should |
| FR-11 | Persist scenarios and run history | Should |
| FR-12 | Compare additional objective configurations | Could |
| FR-13 | Add employee preferences and rest rules | Future |

## 7. Scheduling rules

### Hard constraints in MVP
- Staffing demand must be met for each unit and shift in an accepted complete schedule.
- An employee can only be assigned when available.
- An employee can only be assigned to a unit for which they are qualified.
- An employee may be assigned to at most one unit in a shift.
- Total scheduled hours must not exceed the employee's configured maximum.

If coverage is impossible, the system should report infeasibility or explicit shortages. It must not silently drop requirements.

### Objective
The baseline objective must be explicit in configuration and documentation. If assignment cost values are available, minimise the sum of assignment costs. If no credible cost data is available, use a documented proxy objective or a feasibility objective and do not claim monetary savings.

Fairness may be implemented as a separate, measurable objective, such as minimising deviation from target hours. If cost and fairness are combined, normalise the terms and document weights; a two-stage approach is also acceptable. Never soften a hard constraint by putting it only in a penalty.

## 8. UX requirements

- Desktop-first, responsive layout suitable for a supervisor at a workstation.
- Persistent navigation for Dashboard, Workforce, Production Units, Shift Demand, Schedule Runs and Experiments.
- Dense, readable tables with sticky headers and visible filters.
- Clear status banners for optimal, feasible, infeasible, validation error and solver failure.
- Empty, loading, error and success states for all major screens.
- No neon gradients, gratuitous animation, or emoji-based navigation.
- Accessible keyboard focus, labels, contrast and non-colour status cues.

See `DESIGN.md` for tokens and visual rules.

## 9. Data requirements

Entities:
- Employee: id, display name or code, skills, availability by shift, maximum hours, optional cost attributes.
- Production unit: id, name, required skills or eligibility rules.
- Shift: id, name, start/end, duration.
- Demand: unit, shift, required headcount.
- Scenario: name, planning horizon, input snapshot.
- Schedule run: scenario ID, algorithm, solver status, runtime, objective components, assignments, validation findings.

Minimise personal data. Use fictional/sample employee data in demonstrations unless permission is granted.

## 10. Non-functional requirements

- **Correctness:** accepted complete rosters must pass independent validation.
- **Explainability:** each constraint and metric is documented.
- **Reliability:** solver exceptions are caught and returned as actionable errors.
- **Performance:** define a target after measuring representative instance sizes; do not promise a runtime without benchmark evidence.
- **Security:** validate all API input, configure CORS explicitly, keep secrets out of source control.
- **Accessibility:** meaningful labels, keyboard navigation and non-colour status encoding.
- **Maintainability:** separate UI, API, domain model, solver and validator.

## 11. MVP success measures

- 100% of accepted complete schedules pass all configured hard-constraint checks in test scenarios.
- Infeasible scenarios are surfaced without presenting an invalid roster as successful.
- Every benchmark uses identical input for MILP and Greedy.
- Results include coverage, violations, runtime and workload distribution.
- Cost or overtime claims are made only when the corresponding data and objective are implemented.
- A new user can complete the sample workflow without editing source code.

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Infeasible staffing demand | Explain shortages; report infeasible status |
| Solver unavailable on a machine | Startup capability check and documented setup |
| Incorrect source data | Input validation and scenario preview |
| Fairness objective distorts coverage | Keep coverage hard; normalise soft objectives |
| Results overclaimed | Show solver status and evaluation methodology |
| Scope creep | Defer advanced preferences, integrations and metaheuristics |
| Existing repository differs from proposed layout | Inspect first and extend existing modules |

## 13. Release plan

1. **Foundation:** schema, sample scenario, validator and API contracts.
2. **Optimisation:** MILP and Greedy implementations with tests.
3. **Review UX:** roster, coverage, workload, status and error views.
4. **Evaluation:** controlled benchmark scenarios and comparison report.
5. **Polish:** CSV export, README, demo script and known limitations.
