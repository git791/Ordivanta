from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand
from app.validation.input_validator import validate_scenario


def test_valid_scenario_passes(minimal_valid_scenario: Scenario):
    res = validate_scenario(minimal_valid_scenario)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_duplicate_employee_id(minimal_valid_scenario: Scenario):
    # Add duplicate employee id
    minimal_valid_scenario.employees.append(
        Employee(
            id="E1",  # duplicate with E1
            name="Duplicate E1",
            skills=["assembly"],
            available_shifts=["S1"],
            max_hours=8.0,
        )
    )
    res = validate_scenario(minimal_valid_scenario)
    assert res.is_valid is False
    assert any(e.code == "DUPLICATE_ID" and e.entity_id == "E1" for e in res.errors)


def test_duplicate_unit_id(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.units.append(
        ProductionUnit(id="U1", name="Duplicate Unit", required_skills=["assembly"])
    )
    res = validate_scenario(minimal_valid_scenario)
    assert res.is_valid is False
    assert any(e.code == "DUPLICATE_ID" and e.entity_id == "U1" for e in res.errors)


def test_duplicate_shift_id(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.shifts.append(
        Shift(
            id="S1",
            name="Duplicate Shift",
            start_time="08:00",
            end_time="16:00",
            duration_hours=8.0,
        )
    )
    res = validate_scenario(minimal_valid_scenario)
    assert res.is_valid is False
    assert any(e.code == "DUPLICATE_ID" and e.entity_id == "S1" for e in res.errors)


def test_missing_field_scenario():
    scn = Scenario(id="", name="   ")
    res = validate_scenario(scn)
    assert res.is_valid is False
    assert any(e.code == "MISSING_FIELD" and e.field == "id" for e in res.errors)
    assert any(e.code == "MISSING_FIELD" and e.field == "name" for e in res.errors)


def test_missing_field_entities(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.employees[0].name = ""
    minimal_valid_scenario.units[0].name = ""
    minimal_valid_scenario.shifts[0].start_time = ""
    res = validate_scenario(minimal_valid_scenario)
    assert res.is_valid is False
    assert any(e.code == "MISSING_FIELD" and e.field == "name" for e in res.errors)
    assert any(e.code == "MISSING_FIELD" and e.field == "start_time" for e in res.errors)


def test_unknown_shift_ref_in_demand(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.demands.append(
        Demand(unit_id="U1", shift_id="NON_EXISTENT_SHIFT", required_headcount=1)
    )
    res = validate_scenario(minimal_valid_scenario)
    assert res.is_valid is False
    assert any(e.code == "UNKNOWN_REF" and e.field == "shift_id" for e in res.errors)


def test_unknown_unit_ref_in_demand(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.demands.append(
        Demand(unit_id="NON_EXISTENT_UNIT", shift_id="S1", required_headcount=1)
    )
    res = validate_scenario(minimal_valid_scenario)
    assert res.is_valid is False
    assert any(e.code == "UNKNOWN_REF" and e.field == "unit_id" for e in res.errors)


def test_unknown_shift_in_employee_availability(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.employees[0].available_shifts.append("UNKNOWN_SHIFT")
    res = validate_scenario(minimal_valid_scenario)
    assert res.is_valid is False
    assert any(
        e.code == "UNKNOWN_REF" and e.field == "available_shifts" for e in res.errors
    )


def test_invalid_demand_headcount(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.demands[0].required_headcount = 0
    res = validate_scenario(minimal_valid_scenario)
    assert res.is_valid is False
    assert any(e.code == "INVALID_DEMAND" for e in res.errors)


def test_invalid_shift_duration(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.shifts[0].duration_hours = -2.0
    res = validate_scenario(minimal_valid_scenario)
    assert res.is_valid is False
    assert any(e.code == "INVALID_SHIFT" for e in res.errors)


def test_invalid_employee_hours(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.employees[0].max_hours = 0.0
    res = validate_scenario(minimal_valid_scenario)
    assert res.is_valid is False
    assert any(e.code == "INVALID_HOURS" for e in res.errors)


def test_warn_no_skills(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.employees[0].skills = []
    res = validate_scenario(minimal_valid_scenario)
    # Warnings do not invalidate the scenario
    assert any(w.code == "WARN_NO_SKILLS" for w in res.warnings)


def test_warn_infeasible_cell(minimal_valid_scenario: Scenario):
    # Set demand higher than qualified/available workers
    minimal_valid_scenario.demands[0].required_headcount = 10
    res = validate_scenario(minimal_valid_scenario)
    assert any(w.code == "WARN_INFEASIBLE_CELL" for w in res.warnings)
