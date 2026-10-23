from app.domain.models import Scenario, ValidationResult, ValidationError


def validate_scenario(scenario: Scenario) -> ValidationResult:
    """
    Validate a scenario against input integrity and feasibility rules.
    Returns ValidationResult containing errors and warnings.
    """
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []

    # 1. MISSING_FIELD check on scenario itself
    if not scenario.id or not scenario.id.strip():
        errors.append(
            ValidationError(
                code="MISSING_FIELD",
                message="Scenario ID cannot be empty",
                field="id",
                severity="error",
            )
        )
    if not scenario.name or not scenario.name.strip():
        errors.append(
            ValidationError(
                code="MISSING_FIELD",
                message="Scenario name cannot be empty",
                field="name",
                severity="error",
            )
        )

    # 2. DUPLICATE_ID and entity field validations
    # Employees
    seen_emp_ids: set[str] = set()
    for emp in scenario.employees:
        if not emp.id or not emp.id.strip():
            errors.append(
                ValidationError(
                    code="MISSING_FIELD",
                    message="Employee ID cannot be empty",
                    field="id",
                    severity="error",
                )
            )
        elif emp.id in seen_emp_ids:
            errors.append(
                ValidationError(
                    code="DUPLICATE_ID",
                    message=f"Duplicate employee ID: {emp.id}",
                    field="id",
                    entity_id=emp.id,
                    severity="error",
                )
            )
        else:
            seen_emp_ids.add(emp.id)

        if not emp.name or not emp.name.strip():
            errors.append(
                ValidationError(
                    code="MISSING_FIELD",
                    message=f"Employee '{emp.id}' name cannot be empty",
                    field="name",
                    entity_id=emp.id,
                    severity="error",
                )
            )

        # INVALID_HOURS
        if emp.max_hours <= 0:
            errors.append(
                ValidationError(
                    code="INVALID_HOURS",
                    message=f"Employee '{emp.id}' max_hours must be positive, got {emp.max_hours}",
                    field="max_hours",
                    entity_id=emp.id,
                    severity="error",
                )
            )

        # WARN_NO_SKILLS
        if not emp.skills:
            warnings.append(
                ValidationError(
                    code="WARN_NO_SKILLS",
                    message=f"Employee '{emp.id}' has no skills listed",
                    field="skills",
                    entity_id=emp.id,
                    severity="warning",
                )
            )

    # Units
    seen_unit_ids: set[str] = set()
    for unit in scenario.units:
        if not unit.id or not unit.id.strip():
            errors.append(
                ValidationError(
                    code="MISSING_FIELD",
                    message="Production unit ID cannot be empty",
                    field="id",
                    severity="error",
                )
            )
        elif unit.id in seen_unit_ids:
            errors.append(
                ValidationError(
                    code="DUPLICATE_ID",
                    message=f"Duplicate production unit ID: {unit.id}",
                    field="id",
                    entity_id=unit.id,
                    severity="error",
                )
            )
        else:
            seen_unit_ids.add(unit.id)

        if not unit.name or not unit.name.strip():
            errors.append(
                ValidationError(
                    code="MISSING_FIELD",
                    message=f"Production unit '{unit.id}' name cannot be empty",
                    field="name",
                    entity_id=unit.id,
                    severity="error",
                )
            )

    # Shifts
    seen_shift_ids: set[str] = set()
    for shift in scenario.shifts:
        if not shift.id or not shift.id.strip():
            errors.append(
                ValidationError(
                    code="MISSING_FIELD",
                    message="Shift ID cannot be empty",
                    field="id",
                    severity="error",
                )
            )
        elif shift.id in seen_shift_ids:
            errors.append(
                ValidationError(
                    code="DUPLICATE_ID",
                    message=f"Duplicate shift ID: {shift.id}",
                    field="id",
                    entity_id=shift.id,
                    severity="error",
                )
            )
        else:
            seen_shift_ids.add(shift.id)

        if not shift.name or not shift.name.strip():
            errors.append(
                ValidationError(
                    code="MISSING_FIELD",
                    message=f"Shift '{shift.id}' name cannot be empty",
                    field="name",
                    entity_id=shift.id,
                    severity="error",
                )
            )
        if not shift.start_time or not shift.start_time.strip():
            errors.append(
                ValidationError(
                    code="MISSING_FIELD",
                    message=f"Shift '{shift.id}' start_time cannot be empty",
                    field="start_time",
                    entity_id=shift.id,
                    severity="error",
                )
            )
        if not shift.end_time or not shift.end_time.strip():
            errors.append(
                ValidationError(
                    code="MISSING_FIELD",
                    message=f"Shift '{shift.id}' end_time cannot be empty",
                    field="end_time",
                    entity_id=shift.id,
                    severity="error",
                )
            )

        # INVALID_SHIFT
        if shift.duration_hours <= 0:
            errors.append(
                ValidationError(
                    code="INVALID_SHIFT",
                    message=f"Shift '{shift.id}' duration_hours must be positive, got {shift.duration_hours}",
                    field="duration_hours",
                    entity_id=shift.id,
                    severity="error",
                )
            )

    # 3. Reference integrity checks
    # Check employee.available_shifts reference valid shift IDs
    for emp in scenario.employees:
        for s_id in emp.available_shifts:
            if s_id not in seen_shift_ids:
                errors.append(
                    ValidationError(
                        code="UNKNOWN_REF",
                        message=f"Employee '{emp.id}' references unknown shift '{s_id}'",
                        field="available_shifts",
                        entity_id=emp.id,
                        severity="error",
                    )
                )

    # Check demands
    unit_map = {u.id: u for u in scenario.units}
    for demand in scenario.demands:
        if not demand.unit_id or not demand.unit_id.strip():
            errors.append(
                ValidationError(
                    code="MISSING_FIELD",
                    message="Demand unit_id cannot be empty",
                    field="unit_id",
                    severity="error",
                )
            )
        elif demand.unit_id not in seen_unit_ids:
            errors.append(
                ValidationError(
                    code="UNKNOWN_REF",
                    message=f"Demand references unknown unit '{demand.unit_id}'",
                    field="unit_id",
                    entity_id=demand.unit_id,
                    severity="error",
                )
            )

        if not demand.shift_id or not demand.shift_id.strip():
            errors.append(
                ValidationError(
                    code="MISSING_FIELD",
                    message="Demand shift_id cannot be empty",
                    field="shift_id",
                    severity="error",
                )
            )
        elif demand.shift_id not in seen_shift_ids:
            errors.append(
                ValidationError(
                    code="UNKNOWN_REF",
                    message=f"Demand references unknown shift '{demand.shift_id}'",
                    field="shift_id",
                    entity_id=demand.shift_id,
                    severity="error",
                )
            )

        # INVALID_DEMAND
        if demand.required_headcount <= 0:
            errors.append(
                ValidationError(
                    code="INVALID_DEMAND",
                    message=f"Demand for unit '{demand.unit_id}', shift '{demand.shift_id}' required_headcount must be positive, got {demand.required_headcount}",
                    field="required_headcount",
                    entity_id=f"{demand.unit_id}_{demand.shift_id}",
                    severity="error",
                )
            )

    # 4. WARN_INFEASIBLE_CELL check
    # For any demand cell (unit, shift), check count of employees available AND qualified
    for demand in scenario.demands:
        if demand.unit_id in unit_map and demand.shift_id in seen_shift_ids and demand.required_headcount > 0:
            target_unit = unit_map[demand.unit_id]
            eligible_count = 0
            for emp in scenario.employees:
                is_available = demand.shift_id in emp.available_shifts
                is_qualified = (
                    len(target_unit.required_skills) == 0
                    or any(sk in target_unit.required_skills for sk in emp.skills)
                )
                if is_available and is_qualified:
                    eligible_count += 1

            if eligible_count < demand.required_headcount:
                warnings.append(
                    ValidationError(
                        code="WARN_INFEASIBLE_CELL",
                        message=(
                            f"Demand cell (unit='{demand.unit_id}', shift='{demand.shift_id}') "
                            f"requires {demand.required_headcount} workers, but only {eligible_count} "
                            f"qualified and available employees exist"
                        ),
                        field="required_headcount",
                        entity_id=f"{demand.unit_id}_{demand.shift_id}",
                        severity="warning",
                    )
                )

    return ValidationResult(errors=errors, warnings=warnings)
