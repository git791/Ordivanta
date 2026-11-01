"""
Independent schedule validator.

Validates extracted assignments against the original scenario's ground truth rules.
Does NOT rely on internal solver state.

Validation codes reported:
    Hard errors (is_valid = False):
        ABSENT_EMPLOYEE_ASSIGNED   — employee flagged is_absent is assigned
        AVAILABILITY_VIOLATION     — shift not in employee.available_shifts
        QUALIFICATION_VIOLATION    — employee does not meet unit skill requirements
        MISSING_MANDATORY_SKILL    — ALL/LEVEL_AND_CERT policy: skill missing
        INSUFFICIENT_SKILL_LEVEL   — LEVEL_AND_CERT policy: proficiency too low
        MISSING_CERTIFICATION      — LEVEL_AND_CERT policy: certification missing
        DUPLICATE_ASSIGNMENT       — employee assigned >1 time in same shift
        TEMPORAL_CONFLICT          — overlapping shifts or min-rest violation
        HOURS_EXCEEDED             — total assigned hours exceed max_hours
        UNAUTHORIZED_OVERTIME      — hours exceed regular_hours_limit but overtime_opt_in=False
        OVERTIME_CAP_EXCEEDED      — overtime hours exceed max_overtime_hours
        LOCKED_ASSIGNMENT_CHANGED  — locked assignment was modified

    Warnings (is_valid remains True):
        COVERAGE_SHORTFALL         — fewer assigned than required_headcount
        SHORTAGE_NO_QUALIFIED      — no qualified employee exists for demand cell
        SHORTAGE_UNAVAILABLE       — qualified employees exist but none available
        SHORTAGE_REST_PREVENTS     — rest constraint prevents all qualified available staff
        SHORTAGE_OVERTIME_BLOCKED  — overtime would help but not authorized
"""
from app.domain.models import Assignment, Scenario, ValidationResult, ValidationError
from app.domain.temporal import build_shift_conflict_pairs, shifts_conflict
from app.domain.enums import QualificationPolicy
from app.domain.qualification import is_qualified, qualification_gap_reason


def validate_assignments(
    assignments: list[Assignment],
    scenario: Scenario,
    min_rest_hours: float = 0.0,
    qualification_policy: QualificationPolicy = QualificationPolicy.ANY,
    locked_assignments: list[Assignment] | None = None,
) -> ValidationResult:
    """
    Independently validate extracted assignments against the scenario's ground truth rules.

    Parameters
    ----------
    assignments : list[Assignment]
        The roster assignments to validate.
    scenario : Scenario
        The original scenario (employees, units, shifts, demands).
    min_rest_hours : float
        Minimum rest gap required between consecutive shifts (hours).
    qualification_policy : QualificationPolicy
        The policy used when validating skill qualification.
    locked_assignments : list[Assignment] | None
        Original locked assignments that must not be changed. If None, no lock
        validation is performed.

    Returns
    -------
    ValidationResult
        errors: hard constraint violations (assignments are invalid).
        warnings: soft issues (coverage shortfall, shortage explanations).
    """
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []

    emp_map = {e.id: e for e in scenario.employees}
    unit_map = {u.id: u for u in scenario.units}
    shift_map = {s.id: s for s in scenario.shifts}

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

        # 0. ABSENT_EMPLOYEE_ASSIGNED
        if emp is not None and emp.is_absent:
            errors.append(
                ValidationError(
                    code="ABSENT_EMPLOYEE_ASSIGNED",
                    message=(
                        f"Employee '{a.employee_id}' is marked absent"
                        + (f" ({emp.absence_reason})" if emp.absence_reason else "")
                        + f" but was assigned to shift '{a.shift_id}'"
                    ),
                    field="is_absent",
                    entity_id=a.employee_id,
                    severity="error",
                    employee_id=a.employee_id,
                    unit_id=a.unit_id,
                    shift_id=a.shift_id,
                )
            )

        # 1. AVAILABILITY_VIOLATION
        if emp is not None and not emp.is_absent:
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

        # 2. QUALIFICATION checks (policy-aware)
        if emp is not None and unit is not None and not emp.is_absent:
            if not is_qualified(emp, unit, qualification_policy):
                gap = qualification_gap_reason(emp, unit, qualification_policy)

                if qualification_policy == QualificationPolicy.LEVEL_AND_CERTIFICATION:
                    # Distinguish the specific failure mode
                    emp_skill_set = set(emp.skills)
                    for req in (unit.mandatory_skill_requirements or []):
                        if req.skill not in emp_skill_set:
                            errors.append(
                                ValidationError(
                                    code="MISSING_MANDATORY_SKILL",
                                    message=f"Employee '{a.employee_id}' missing mandatory skill '{req.skill}' for unit '{a.unit_id}'",
                                    field="skills",
                                    entity_id=a.employee_id,
                                    severity="error",
                                    employee_id=a.employee_id,
                                    unit_id=a.unit_id,
                                    shift_id=a.shift_id,
                                )
                            )
                        else:
                            emp_level = emp.skill_levels.get(req.skill, 1)
                            if emp_level < req.min_level:
                                errors.append(
                                    ValidationError(
                                        code="INSUFFICIENT_SKILL_LEVEL",
                                        message=(
                                            f"Employee '{a.employee_id}' has skill '{req.skill}' "
                                            f"at level {emp_level}, but unit '{a.unit_id}' requires level {req.min_level}"
                                        ),
                                        field="skill_levels",
                                        entity_id=a.employee_id,
                                        severity="error",
                                        employee_id=a.employee_id,
                                        unit_id=a.unit_id,
                                        shift_id=a.shift_id,
                                    )
                                )
                    # Check certifications
                    if unit.required_certifications:
                        emp_certs = set(emp.certifications)
                        for cert in unit.required_certifications:
                            if cert not in emp_certs:
                                errors.append(
                                    ValidationError(
                                        code="MISSING_CERTIFICATION",
                                        message=f"Employee '{a.employee_id}' missing required certification '{cert}' for unit '{a.unit_id}'",
                                        field="certifications",
                                        entity_id=a.employee_id,
                                        severity="error",
                                        employee_id=a.employee_id,
                                        unit_id=a.unit_id,
                                        shift_id=a.shift_id,
                                    )
                                )
                elif qualification_policy == QualificationPolicy.ALL:
                    errors.append(
                        ValidationError(
                            code="QUALIFICATION_VIOLATION",
                            message=gap or (
                                f"Employee '{a.employee_id}' does not meet ALL skill requirements "
                                f"for unit '{a.unit_id}' (requires all of {unit.required_skills}, has {emp.skills})"
                            ),
                            field="skills",
                            entity_id=a.employee_id,
                            severity="error",
                            employee_id=a.employee_id,
                            unit_id=a.unit_id,
                            shift_id=a.shift_id,
                        )
                    )
                else:
                    # ANY policy
                    if unit.required_skills:
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

    # 5. HOURS checks
    for emp_id, total_hours in emp_total_hours.items():
        emp = emp_map.get(emp_id)
        if emp is None:
            continue

        # HOURS_EXCEEDED: total > hard maximum (max_hours or effective_max_hours)
        hard_max = emp.effective_max_hours()
        if total_hours > hard_max:
            errors.append(
                ValidationError(
                    code="HOURS_EXCEEDED",
                    message=(
                        f"Employee '{emp_id}' assigned {total_hours}h which exceeds "
                        f"maximum allowed {hard_max}h"
                    ),
                    field="max_hours",
                    entity_id=emp_id,
                    severity="error",
                    employee_id=emp_id,
                )
            )

        # UNAUTHORIZED_OVERTIME: hours exceed regular_hours_limit but no consent
        if emp.regular_hours_limit is not None and not emp.overtime_opt_in:
            if total_hours > emp.regular_hours_limit:
                errors.append(
                    ValidationError(
                        code="UNAUTHORIZED_OVERTIME",
                        message=(
                            f"Employee '{emp_id}' assigned {total_hours}h which exceeds "
                            f"regular limit {emp.regular_hours_limit}h, but overtime_opt_in is False"
                        ),
                        field="overtime_opt_in",
                        entity_id=emp_id,
                        severity="error",
                        employee_id=emp_id,
                    )
                )

        # OVERTIME_CAP_EXCEEDED: overtime hours exceed max_overtime_hours
        if emp.overtime_opt_in and emp.regular_hours_limit is not None:
            overtime_hours = max(0.0, total_hours - emp.regular_hours_limit)
            if overtime_hours > emp.max_overtime_hours:
                errors.append(
                    ValidationError(
                        code="OVERTIME_CAP_EXCEEDED",
                        message=(
                            f"Employee '{emp_id}' has {overtime_hours}h overtime "
                            f"which exceeds cap {emp.max_overtime_hours}h"
                        ),
                        field="max_overtime_hours",
                        entity_id=emp_id,
                        severity="error",
                        employee_id=emp_id,
                    )
                )

    # 6. LOCKED_ASSIGNMENT_CHANGED check
    if locked_assignments:
        locked_set = {(a.employee_id, a.unit_id, a.shift_id) for a in locked_assignments}
        assigned_set = {(a.employee_id, a.unit_id, a.shift_id) for a in assignments}
        for locked_key in locked_set:
            if locked_key not in assigned_set:
                emp_id, unit_id, shift_id = locked_key
                errors.append(
                    ValidationError(
                        code="LOCKED_ASSIGNMENT_CHANGED",
                        message=(
                            f"Locked assignment (employee='{emp_id}', unit='{unit_id}', "
                            f"shift='{shift_id}') was removed or changed"
                        ),
                        field="is_locked",
                        entity_id=emp_id,
                        severity="error",
                        employee_id=emp_id,
                        unit_id=unit_id,
                        shift_id=shift_id,
                    )
                )

    # 7. COVERAGE_SHORTFALL check + shortage diagnostic warnings
    cell_counts: dict[tuple[str, str], int] = {}
    for a in assignments:
        key = (a.unit_id, a.shift_id)
        cell_counts[key] = cell_counts.get(key, 0) + 1

    # Pre-compute conflict map for shortage diagnostics
    conflict_map = {}
    if scenario.shifts:
        from app.domain.temporal import build_shift_conflict_map
        conflict_map = build_shift_conflict_map(scenario.shifts, min_rest_hours=min_rest_hours)

    for demand in scenario.demands:
        key = (demand.unit_id, demand.shift_id)
        filled = cell_counts.get(key, 0)
        if filled < demand.required_headcount:
            shortage = demand.required_headcount - filled
            warnings.append(
                ValidationError(
                    code="COVERAGE_SHORTFALL",
                    message=(
                        f"Unit '{demand.unit_id}' in shift '{demand.shift_id}' requires "
                        f"{demand.required_headcount} staff, but only {filled} assigned "
                        f"(shortage: {shortage})"
                    ),
                    field="demands",
                    entity_id=f"{demand.unit_id}_{demand.shift_id}",
                    severity="warning",
                    unit_id=demand.unit_id,
                    shift_id=demand.shift_id,
                )
            )

            # Diagnostic: explain why the shortage occurred
            unit = unit_map.get(demand.unit_id)
            if unit is not None:
                _add_shortage_explanation(
                    warnings=warnings,
                    demand=demand,
                    unit=unit,
                    employees=scenario.employees,
                    assignments=assignments,
                    qualification_policy=qualification_policy,
                    conflict_map=conflict_map,
                )

    return ValidationResult(errors=errors, warnings=warnings)


def _add_shortage_explanation(
    warnings: list[ValidationError],
    demand,
    unit,
    employees,
    assignments: list[Assignment],
    qualification_policy: QualificationPolicy,
    conflict_map: dict[str, set[str]],
) -> None:
    """
    Add a heuristic diagnostic warning explaining why a shortage occurred.

    NOTE: These explanations are heuristic only. They identify likely causes
    based on the employee pool but are not mathematically exhaustive proofs.
    """
    shift_id = demand.shift_id
    unit_id = demand.unit_id

    # Currently assigned employees for this shift
    assigned_emp_ids = {a.employee_id for a in assignments if a.shift_id == shift_id}

    qualified_count = 0
    available_count = 0
    rest_blocked_count = 0
    ot_blocked_count = 0

    for emp in employees:
        if emp.is_absent:
            continue
        if not is_qualified(emp, unit, qualification_policy):
            continue
        qualified_count += 1
        if shift_id not in emp.available_shifts:
            continue
        available_count += 1
        # Check if rest constraint would prevent assignment
        if any(s in conflict_map.get(shift_id, set()) for s in emp.available_shifts if s != shift_id):
            rest_blocked_count += 1
        # Check overtime
        if emp.regular_hours_limit is not None and not emp.overtime_opt_in:
            ot_blocked_count += 1

    if qualified_count == 0:
        warnings.append(
            ValidationError(
                code="SHORTAGE_NO_QUALIFIED",
                message=(
                    f"Unit '{unit_id}' shift '{shift_id}': no qualified (non-absent) employee "
                    f"exists under policy {qualification_policy.value}"
                ),
                field="demands",
                entity_id=f"{unit_id}_{shift_id}",
                severity="warning",
                unit_id=unit_id,
                shift_id=shift_id,
            )
        )
    elif available_count == 0:
        warnings.append(
            ValidationError(
                code="SHORTAGE_UNAVAILABLE",
                message=(
                    f"Unit '{unit_id}' shift '{shift_id}': {qualified_count} qualified employees "
                    f"exist but none are available for this shift"
                ),
                field="demands",
                entity_id=f"{unit_id}_{shift_id}",
                severity="warning",
                unit_id=unit_id,
                shift_id=shift_id,
            )
        )
    elif rest_blocked_count > 0 and available_count <= rest_blocked_count:
        warnings.append(
            ValidationError(
                code="SHORTAGE_REST_PREVENTS",
                message=(
                    f"Unit '{unit_id}' shift '{shift_id}': rest constraints may prevent "
                    f"assignment of {rest_blocked_count} of {available_count} available qualified employees"
                ),
                field="demands",
                entity_id=f"{unit_id}_{shift_id}",
                severity="warning",
                unit_id=unit_id,
                shift_id=shift_id,
            )
        )
    elif ot_blocked_count > 0:
        warnings.append(
            ValidationError(
                code="SHORTAGE_OVERTIME_BLOCKED",
                message=(
                    f"Unit '{unit_id}' shift '{shift_id}': {ot_blocked_count} of {available_count} "
                    f"available qualified employees cannot work overtime (overtime_opt_in=False)"
                ),
                field="demands",
                entity_id=f"{unit_id}_{shift_id}",
                severity="warning",
                unit_id=unit_id,
                shift_id=shift_id,
            )
        )
