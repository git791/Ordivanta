# Skill: Ordivanta Frontend and UX

## Purpose
Build an accessible industrial scheduling console using the existing Next.js/React/TypeScript codebase.

## Before coding
- Inspect the existing routes, component library, Tailwind setup, fonts and tokens.
- Reuse established components; do not create a second design system.
- Read `docs/DESIGN.md`.
- Confirm the API contract rather than inventing response fields.

## Visual principles
- Cool neutral canvas, white surfaces, steel-blue primary action.
- IBM Plex Sans or the repository's existing approved sans-serif; tabular numerals for metrics.
- Dense, legible tables with filters and sticky headers where useful.
- Restrained borders and shadows.
- No Streamlit, neon, excessive gradients, emoji navigation or unnecessary motion.
- Use status text and iconography in addition to colour.

## Main workflows
1. Dashboard and scenario selection.
2. Workforce and qualification management.
3. Unit demand and shift configuration.
4. Input validation and review.
5. Schedule run configuration.
6. Results with roster, coverage, workload and violations.
7. MILP/Greedy comparison and export.

## Interaction requirements
- Show loading state while a run is executing.
- Explain validation errors and identify the affected entity.
- Distinguish optimal, feasible, infeasible, not solved and error.
- Never display a fake progress percentage.
- Do not enable “approve/export complete roster” when required coverage is missing unless the export is clearly marked incomplete.
- Ensure keyboard focus, accessible names, responsive layout and empty states.

## Verification
- Test forms, filters, loading/errors, result statuses and export affordances.
- Check narrow layouts and keyboard-only navigation.
- Confirm all displayed metrics come from actual API data, not hard-coded demo values.
