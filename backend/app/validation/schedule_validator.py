from app.domain.models import Assignment, Scenario, ValidationResult, ValidationError
from app.domain.temporal import build_shift_conflict_pairs, shifts_conflict


def validate_assignments(
    assignments: list[Assignment],
    scenario: Scenario,
    min_rest_hours: float = 0.0,
) -> ValidationResult:
    """
    Independently validate extracted assignments against the scenario's ground truth rules.
    Does NOT rely on internal solver state.
    """
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []

    emp_map = {e.id: e for e in scenario.employees}
    unit_map = {u.id: u for u in scenario.units}

    # Tracking structures
    emp_shift_assignments: dict[str, dict[str, int]] = {}
    emp_total_hours: dict[str, float] = {}

    for a in assignments:
        emp = emp_map.get(a.employee_id)
        unit = unit_map.get(a.unit_id)

        # Track hours
        emp_total_hours[a.employee_id] = emp_total_hours.get(a.employee_id, 0.0) + a.hours

        # Track shift assignments for duplicate checking
        if a.employee_id not in emp_shift_assignments:
            emp_shift_assignments[a.employee_id] = {}
        emp_shift_assignments[a.employee_id][a.shift_id] = (
            emp_shift_assignments[a.employee_id].get(a.shift_id, 0) + 1
        )

        # 1. AVAILABILITY_VIOLATION
        if emp is not None:
            if a.shift_id not in emp.available_shifts:
                errors.append(
                    ValidationError(
                        code="AVAILABILITY_VIOLATION",
                        message=f"Employee '{a.employee_id}' assigned to shift '{a.shift_id}' for which they are unavailable",
                        field="available_shifts",
                        entity_id=a.employee_id,
                        severity="error",
                        employee_id=a.employee_id,
                        unit_id=a.unit_id,
                        shift_id=a.shift_id,
                    )
                )

        # 2. QUALIFICATION_VIOLATION
        if emp is not None and unit is not None:
            if unit.required_skills:
                is_qualified = any(sk in unit.required_skills for sk in emp.skills)
                if not is_qualified:
                    errors.append(
                        ValidationError(
                            code="QUALIFICATION_VIOLATION",
                            message=(
                                f"Employee '{a.employee_id}' assigned to unit '{a.unit_id}' "
                                f"without required skills (requires one of {unit.required_skills}, has {emp.skills})"
                            ),
                            field="skills",
                            entity_id=a.employee_id,
                            severity="error",
                            employee_id=a.employee_id,
                            unit_id=a.unit_id,
                            shift_id=a.shift_id,
                        )
                    )

    # 3. DUPLICATE_ASSIGNMENT check (>1 assignment in the same shift)
    for emp_id, shift_counts in emp_shift_assignments.items():
        for shift_id, count in shift_counts.items():
            if count > 1:
                errors.append(
                    ValidationError(
                        code="DUPLICATE_ASSIGNMENT",
                        message=f"Employee '{emp_id}' assigned {count} times to shift '{shift_id}'",
                        field="shift_id",
                        entity_id=emp_id,
                        severity="error",
                        employee_id=emp_id,
                        shift_id=shift_id,
                    )
                )

    # 4. TEMPORAL_CONFLICT check (overlapping shifts or minimum rest violation)
    shift_map = {s.id: s for s in scenario.shifts}
    for emp_id, shift_counts in emp_shift_assignments.items():
        distinct_shifts = list(shift_counts.keys())
        n_shifts = len(distinct_shifts)
        for idx1 in range(n_shifts):
            for idx2 in range(idx1 + 1, n_shifts):
                s1_id = distinct_shifts[idx1]
                s2_id = distinct_shifts[idx2]
                s1 = shift_map.get(s1_id)
                s2 = shift_map.get(s2_id)
                if s1 is not None and s2 is not None:
                    is_conf, conf_type = shifts_conflict(s1, s2, min_rest_hours=min_rest_hours)
                    if is_conf:
                        code = conf_type or "TEMPORAL_CONFLICT"
                        errors.append(
                            ValidationError(
                                code=code,
                                message=(
                                    f"Employee '{emp_id}' assigned to conflicting shifts "
                                    f"'{s1_id}' and '{s2_id}' ({code})"
                                ),
                                field="shift_id",
                                entity_id=emp_id,
                                severity="error",
                                employee_id=emp_id,
                                shift_id=s2_id,
                            )
                        )

    # 4. HOURS_EXCEEDED check
    for emp_id, total_hours in emp_total_hours.items():
        emp = emp_map.get(emp_id)
        if emp is not None and total_hours > emp.max_hours:
            errors.append(
                ValidationError(
                    code="HOURS_EXCEEDED",
                    message=(
                        f"Employee '{emp_id}' assigned {total_hours}h which exceeds maximum allowed {emp.max_hours}h"
                    ),
                    field="max_hours",
                    entity_id=emp_id,
                    severity="error",
                    employee_id=emp_id,
                )
            )

    # 5. COVERAGE_SHORTFALL check (warning per demand cell)
    # Count assignments per (unit_id, shift_id)
    cell_counts: dict[tuple[str, str], int] = {}
    for a in assignments:
        key = (a.unit_id, a.shift_id)
        cell_counts[key] = cell_counts.get(key, 0) + 1

    for demand in scenario.demands:
        key = (demand.unit_id, demand.shift_id)
        filled = cell_counts.get(key, 0)
        if filled < demand.required_headcount:
            warnings.append(
                ValidationError(
                    code="COVERAGE_SHORTFALL",
                    message=(
                        f"Unit '{demand.unit_id}' in shift '{demand.shift_id}' requires "
                        f"{demand.required_headcount} staff, but only {filled} assigned"
                    ),
                    field="demands",
                    entity_id=f"{demand.unit_id}_{demand.shift_id}",
                    severity="warning",
                    unit_id=demand.unit_id,
                    shift_id=demand.shift_id,
                )
            )

    return ValidationResult(errors=errors, warnings=warnings)
