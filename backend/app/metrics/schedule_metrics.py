from app.domain.models import Assignment, Scenario
from app.schemas.schedule import MetricsResponse
import statistics


def compute_coverage(
    assignments: list[Assignment],
    scenario: Scenario,
) -> tuple[int, int, float]:
    """
    Compute demand coverage metrics.

    Returns:
        tuple[int, int, float]: (total_filled_positions, total_required_positions, coverage_pct)

    Rules:
    - total_required_positions = sum(d.required_headcount for d in scenario.demands)
    - Fulfilled headcount per (unit_id, shift_id) cell is min(assigned, required).
    - Surplus assignments in one cell never compensate for deficits in another cell.
    - Coverage percentage cannot exceed 100.0%.
    - If total_required_positions == 0, coverage_pct is 100.0%.
    """
    total_required = sum(d.required_headcount for d in scenario.demands)
    if total_required == 0:
        return 0, 0, 100.0

    filled_per_cell: dict[tuple[str, str], int] = {}
    for a in assignments:
        key = (a.unit_id, a.shift_id)
        filled_per_cell[key] = filled_per_cell.get(key, 0) + 1

    total_filled = 0
    for d in scenario.demands:
        key = (d.unit_id, d.shift_id)
        filled = filled_per_cell.get(key, 0)
        total_filled += min(filled, d.required_headcount)

    coverage_pct = min(100.0, round((total_filled / total_required) * 100.0, 1))
    return total_filled, total_required, coverage_pct


def compute_metrics(
    assignments: list[Assignment],
    scenario: Scenario,
    runtime_seconds: float,
    objective_value: float | None,
    violation_count: int,
) -> MetricsResponse:
    """Compute schedule quality and operational metrics."""
    total_filled, total_required, coverage_pct = compute_coverage(assignments, scenario)
    unfilled = max(0, total_required - total_filled)
    coverage_rate = (total_filled / total_required) if total_required > 0 else 1.0

    # Employee hours calculation
    emp_hours: dict[str, float] = {}
    for a in assignments:
        emp_hours[a.employee_id] = emp_hours.get(a.employee_id, 0.0) + a.hours

    spread = statistics.stdev(emp_hours.values()) if len(emp_hours) > 1 else None

    return MetricsResponse(
        coverage_rate=round(coverage_rate, 4),
        unfilled_positions=unfilled,
        hard_constraint_violations=violation_count,
        employee_hours=emp_hours,
        workload_spread=round(spread, 4) if spread is not None else None,
        runtime_seconds=round(runtime_seconds, 4),
        objective_value=round(objective_value, 4) if objective_value is not None else None,
        total_required_positions=total_required,
        total_filled_positions=total_filled,
    )

