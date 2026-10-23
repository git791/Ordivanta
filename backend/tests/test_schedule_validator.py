from app.domain.models import Scenario, Assignment
from app.validation.schedule_validator import validate_assignments


def test_valid_assignments(minimal_valid_scenario: Scenario):
    assignments = [
        Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
        Assignment(employee_id="E2", unit_id="U1", shift_id="S1", hours=8.0),
    ]
    res = validate_assignments(assignments, minimal_valid_scenario)
    assert res.is_valid is True
    assert len(res.errors) == 0
    assert len(res.warnings) == 0


def test_availability_violation(minimal_valid_scenario: Scenario):
    # E1 is only available for S1, assign to S2
    assignments = [
        Assignment(employee_id="E1", unit_id="U1", shift_id="S2", hours=8.0),
    ]
    res = validate_assignments(assignments, minimal_valid_scenario)
    assert res.is_valid is False
    assert any(
        e.code == "AVAILABILITY_VIOLATION" and e.employee_id == "E1"
        for e in res.errors
    )


def test_qualification_violation(minimal_valid_scenario: Scenario):
    # E1 has "assembly", unit requires "welding"
    minimal_valid_scenario.units[0].required_skills = ["welding"]
    assignments = [
        Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
    ]
    res = validate_assignments(assignments, minimal_valid_scenario)
    assert res.is_valid is False
    assert any(
        e.code == "QUALIFICATION_VIOLATION" and e.employee_id == "E1"
        for e in res.errors
    )


def test_duplicate_assignment(minimal_valid_scenario: Scenario):
    # E1 assigned twice to shift S1 (e.g. to U1 and another unit)
    assignments = [
        Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
        Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
    ]
    res = validate_assignments(assignments, minimal_valid_scenario)
    assert res.is_valid is False
    assert any(
        e.code == "DUPLICATE_ASSIGNMENT" and e.employee_id == "E1"
        for e in res.errors
    )


def test_hours_exceeded(minimal_valid_scenario: Scenario):
    # E1 has max_hours = 8.0, assigned 16.0 hours total
    assignments = [
        Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
        Assignment(employee_id="E1", unit_id="U1", shift_id="S2", hours=8.0),
    ]
    res = validate_assignments(assignments, minimal_valid_scenario)
    assert res.is_valid is False
    assert any(
        e.code == "HOURS_EXCEEDED" and e.employee_id == "E1"
        for e in res.errors
    )


def test_coverage_shortfall(minimal_valid_scenario: Scenario):
    # Demand is 2, but only 1 assigned
    assignments = [
        Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
    ]
    res = validate_assignments(assignments, minimal_valid_scenario)
    # Shortfall is a warning, not a hard violation error
    assert res.is_valid is True
    assert any(w.code == "COVERAGE_SHORTFALL" for w in res.warnings)


def test_tampered_assignment_caught(minimal_valid_scenario: Scenario):
    """
    Simulate a solve output being tampered with by corrupting an assignment's unit.
    The independent validator must catch the qualification violation.
    """
    # Suppose U1 requires "assembly", and we add U2 requiring "special_skill"
    from app.domain.models import ProductionUnit

    minimal_valid_scenario.units.append(
        ProductionUnit(id="U2", name="Special Unit", required_skills=["special_skill"])
    )

    # Valid assignment was E1 -> U1. Tampered assignment assigns E1 -> U2.
    tampered_assignments = [
        Assignment(employee_id="E1", unit_id="U2", shift_id="S1", hours=8.0),
        Assignment(employee_id="E2", unit_id="U1", shift_id="S1", hours=8.0),
    ]

    res = validate_assignments(tampered_assignments, minimal_valid_scenario)
    assert res.is_valid is False
    assert any(
        e.code == "QUALIFICATION_VIOLATION" and e.employee_id == "E1"
        for e in res.errors
    )
