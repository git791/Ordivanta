# Agent Instructions — Ordivanta

## Mission
Build and maintain a reliable workforce scheduling application for manufacturing operations. Optimisation correctness and clear reporting take precedence over visual polish.

## Before changing code
1. Inspect the existing repository, package manifests, routes, modules and tests.
2. Reuse existing components and domain logic; do not restart the project or create duplicate schedulers, validators, API clients or design tokens.
3. Read `README.md`, `docs/PRD.md`, `docs/TECHNICAL_DESIGN.md` and `docs/DESIGN.md`.
4. Identify what is implemented, tested, partially implemented or only planned.
5. Make the smallest coherent change that satisfies the task.

## Architecture boundaries
- Frontend: Next.js + React + TypeScript + Tailwind CSS. **Do not use Streamlit.**
- Backend: FastAPI and Pydantic schemas.
- Optimisation: MILP through PuLP and a configured solver adapter; Greedy is a comparison baseline.
- Keep solver code out of UI components.
- Keep request schemas, domain models, input validation, optimisation, independent schedule validation and metrics logically separate.
- Add dependencies only when needed and verify the project's existing package manager/version conventions.

## Scheduling correctness
- Availability, qualifications, one assignment per employee per shift and maximum scheduled hours are hard constraints in the MVP.
- Coverage is a hard requirement for an accepted complete schedule. If it cannot be satisfied, report infeasibility or explicitly model shortages; never silently present an incomplete roster as fully successful.
- Only report `OPTIMAL` when the solver explicitly proves optimality.
- Distinguish optimal, feasible, infeasible, not solved and error states.
- Independently validate extracted assignments using original input data.
- Do not claim cost minimisation, overtime reduction or fairness improvements unless the associated data, objective and tests exist.
- Never relax hard constraints just to make a demo succeed.

## Code quality
- Use clear names and typed interfaces.
- Validate external inputs at API boundaries.
- Return structured errors with stable codes and useful messages.
- Keep functions small and testable.
- Add or update tests with every change to optimisation or validation logic.
- Avoid hard-coded demo data in production paths; keep fixtures under tests or explicit sample-data modules.
- Do not commit secrets, real employee personal data or machine-specific absolute paths.

## Frontend and design
- Follow `docs/DESIGN.md` tokens and component rules.
- No neon, gratuitous gradients, emoji-based navigation or decorative animations.
- Status must include text, not colour alone.
- Provide loading, empty, error and success states.
- Use accessible labels, keyboard focus and responsive layouts.
- Reuse existing UI components and tokens.

## Testing and verification
- Run focused tests first, then the relevant full test suite.
- For scheduling changes, include feasible and infeasible test cases.
- Test availability, skills, duplicate assignments, hour limits and coverage.
- Report commands run and their actual outcomes; never invent test results.
- If a test cannot run because a dependency/solver is missing, say so and provide the exact blocker.

## Documentation
- Keep README claims aligned with actual implementation.
- Mark roadmap items as planned.
- Include the objective definition and assumptions.
- Record benchmark method and actual measurements before claiming performance improvements.
- Update API documentation when contracts change.

## Task completion format
When completing a code task, report:
1. What changed.
2. Files changed.
3. Tests/checks run and results.
4. Remaining risks or follow-up tasks.

## Agent roles (logical, not necessarily separate autonomous agents)
- **Product/Requirements Agent:** scope, acceptance criteria, assumptions and priorities.
- **Optimisation Agent:** MILP formulation, Greedy baseline, solver statuses and constraint tests.
- **Backend/API Agent:** schemas, endpoints, persistence, error handling and integration tests.
- **Frontend/UX Agent:** accessible workflow, tables, status and responsive UI.
- **QA/Evaluation Agent:** independent validation, edge cases and reproducible benchmarks.

The same developer may perform multiple roles. Roles do not imply work has already been completed.
