# Skill: FastAPI Contracts and Services

## Purpose
Build a predictable API for workforce data, scenarios, schedule runs and metrics.

## Procedure
1. Inspect existing routes and schemas before creating new ones.
2. Use Pydantic request/response models.
3. Validate IDs, cross-references, shift durations and numeric bounds.
4. Keep route handlers thin; delegate to services.
5. Catch solver and persistence failures and map them to clear error responses.
6. Return explicit schedule status, runtime, assignments, metrics and warnings.
7. Configure CORS for known frontend origins only.
8. Add unit and API integration tests.
9. Update README and technical documentation when a contract changes.

## Response principles
- Do not leak stack traces or secrets to the client.
- Use stable error codes.
- Separate invalid request, infeasible model, solver failure and internal server error.
- Avoid exposing personal employee data that is not needed by the caller.
- Do not return a successful-complete status for a roster with unfilled required positions.

## Suggested API areas
- Health.
- Employees/workforce.
- Production units.
- Shifts and demand.
- Scenario validation.
- Schedule solve and run retrieval.
- Metrics and CSV export.

These are logical areas, not instructions to duplicate endpoints that already exist.
