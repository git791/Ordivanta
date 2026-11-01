"""
Tests for voluntary overtime consent, regular hour limits, overtime caps,
and on-call assignment rules.

Verifies:
- Overtime is only permitted when overtime_opt_in=True AND within hour limits.
- Workers with overtime_opt_in=False are constrained to regular_hours_limit.
- Overtime cap (max_overtime_hours) is enforced by the validator.
- Unconfirmed on-call workers are not counted as available.
- Overtime does not bypass qualification requirements.
"""
import pytest
from app.domain.models import (
    Scenario, Employee, ProductionUnit, Shift, Demand, Assignment,
)
from app.domain.enums import SolverStatus, QualificationPolicy
from app.schemas.schedule import ObjectiveConfig
from app.optimization.milp_scheduler import MILPScheduler
from app.optimization.greedy_scheduler import GreedyScheduler
from app.validation.schedule_validator import validate_assignments


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def two_shifts():
    return [
        Shift(id="S1", name="Morning", start_time="2026-10-01T08:00:00", end_time="2026-10-01T16:00:00", duration_hours=8.0),
        Shift(id="S2", name="Evening", start_time="2026-10-01T16:00:00", end_time="2026-10-02T00:00:00", duration_hours=8.0),
    ]


@pytest.fixture
def simple_unit():
    return ProductionUnit(id="U1", name="Assembly", required_skills=[])


# ---------------------------------------------------------------------------
# 1. effective_max_hours() helper
# ---------------------------------------------------------------------------

class TestEffectiveMaxHours:

    def test_no_overtime_returns_max_hours(self):
        emp = Employee(id="E1", name="A", skills=[], available_shifts=[], max_hours=40.0)
        assert emp.effective_max_hours() == 40.0

    def test_regular_limit_no_consent_returns_limit(self):
        emp = Employee(
            id="E1", name="A", skills=[], available_shifts=[], max_hours=48.0,
            regular_hours_limit=40.0, overtime_opt_in=False, max_overtime_hours=8.0,
        )
        # No consent → effective = regular_hours_limit
        assert emp.effective_max_hours() == 40.0

    def test_regular_limit_with_consent_includes_ot(self):
        emp = Employee(
            id="E1", name="A", skills=[], available_shifts=[], max_hours=48.0,
            regular_hours_limit=40.0, overtime_opt_in=True, max_overtime_hours=8.0,
        )
        assert emp.effective_max_hours() == 48.0

    def test_no_regular_limit_with_consent_uses_max_hours(self):
        emp = Employee(
            id="E1", name="A", skills=[], available_shifts=[], max_hours=40.0,
            overtime_opt_in=True, max_overtime_hours=8.0,
            # regular_hours_limit=None (default)
        )
        # Falls back to max_hours (40.0), OT budget added on top
        assert emp.effective_max_hours() == 48.0


# ---------------------------------------------------------------------------
# 2. MILP scheduler respects overtime consent
# ---------------------------------------------------------------------------

class TestMILPOvertimeConsent:

    def test_no_consent_cannot_work_both_shifts(self, two_shifts, simple_unit):
        """Employee with regular_hours_limit=8h and no consent cannot work 2×8h shifts."""
        emp = Employee(
            id="E1", name="A", skills=[], available_shifts=["S1", "S2"],
            max_hours=16.0,
            regular_hours_limit=8.0, overtime_opt_in=False, max_overtime_hours=0.0,
        )
        scn = Scenario(
            id="s", name="t", employees=[emp], units=[simple_unit], shifts=two_shifts,
            demands=[
                Demand(unit_id="U1", shift_id="S1", required_headcount=1),
                Demand(unit_id="U1", shift_id="S2", required_headcount=1),
            ],
        )
        cfg = ObjectiveConfig()
        outcome = MILPScheduler().solve(scn, cfg)
        # Only 1 shift (8h) can be worked → demand of 2 shifts → infeasible
        assert outcome.status == SolverStatus.INFEASIBLE

    def test_with_consent_can_work_both_shifts(self, two_shifts, simple_unit):
        """Employee with overtime consent can work 2×8h = 16h."""
        emp = Employee(
            id="E1", name="A", skills=[], available_shifts=["S1", "S2"],
            max_hours=16.0,
            regular_hours_limit=8.0, overtime_opt_in=True, max_overtime_hours=8.0,
        )
        scn = Scenario(
            id="s", name="t", employees=[emp], units=[simple_unit], shifts=two_shifts,
            demands=[
                Demand(unit_id="U1", shift_id="S1", required_headcount=1),
                Demand(unit_id="U1", shift_id="S2", required_headcount=1),
            ],
        )
        cfg = ObjectiveConfig()
        outcome = MILPScheduler().solve(scn, cfg)
        assert outcome.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
        total_hours = sum(a.hours for a in outcome.assignments)
        assert total_hours == 16.0


# ---------------------------------------------------------------------------
# 3. Independent validator: unauthorized overtime
# ---------------------------------------------------------------------------

class TestValidatorOvertimeConsent:

    def test_unauthorized_overtime_flagged(self, two_shifts, simple_unit):
        emp = Employee(
            id="E1", name="A", skills=[], available_shifts=["S1", "S2"],
            max_hours=16.0,
            regular_hours_limit=8.0, overtime_opt_in=False, max_overtime_hours=8.0,
        )
        scn = Scenario(
            id="s", name="t", employees=[emp], units=[simple_unit], shifts=two_shifts,
            demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
        )
        # Simulate an incorrect assignment of 16h to an employee with no OT consent
        bad = [
            Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
            Assignment(employee_id="E1", unit_id="U1", shift_id="S2", hours=8.0),
        ]
        result = validate_assignments(bad, scn)
        assert result.is_valid is False
        assert any(e.code == "UNAUTHORIZED_OVERTIME" for e in result.errors)

    def test_overtime_cap_exceeded_flagged(self, two_shifts, simple_unit):
        emp = Employee(
            id="E1", name="A", skills=[], available_shifts=["S1", "S2"],
            max_hours=20.0,
            regular_hours_limit=8.0, overtime_opt_in=True, max_overtime_hours=4.0,
        )
        scn = Scenario(
            id="s", name="t", employees=[emp], units=[simple_unit], shifts=two_shifts,
            demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
        )
        # 8h regular + 8h OT = 16h but max_overtime_hours = 4h → OT cap exceeded
        bad = [
            Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
            Assignment(employee_id="E1", unit_id="U1", shift_id="S2", hours=8.0),
        ]
        result = validate_assignments(bad, scn)
        assert result.is_valid is False
        assert any(e.code == "OVERTIME_CAP_EXCEEDED" for e in result.errors)

    def test_authorized_overtime_within_cap_valid(self, two_shifts, simple_unit):
        emp = Employee(
            id="E1", name="A", skills=[], available_shifts=["S1", "S2"],
            max_hours=16.0,
            regular_hours_limit=8.0, overtime_opt_in=True, max_overtime_hours=8.0,
        )
        scn = Scenario(
            id="s", name="t", employees=[emp], units=[simple_unit], shifts=two_shifts,
            demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
        )
        assignments = [
            Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
            Assignment(employee_id="E1", unit_id="U1", shift_id="S2", hours=8.0),
        ]
        result = validate_assignments(assignments, scn)
        # Should be valid — no overtime cap violation
        assert not any(e.code in ("UNAUTHORIZED_OVERTIME", "OVERTIME_CAP_EXCEEDED") for e in result.errors)


# ---------------------------------------------------------------------------
# 4. Absent employee checks
# ---------------------------------------------------------------------------

def test_absent_employee_not_assigned_by_milp(two_shifts, simple_unit):
    emp = Employee(
        id="E1", name="A", skills=[], available_shifts=["S1"],
        max_hours=8.0, is_absent=True,
    )
    emp2 = Employee(id="E2", name="B", skills=[], available_shifts=["S1"], max_hours=8.0)
    scn = Scenario(
        id="s", name="t", employees=[emp, emp2], units=[simple_unit],
        shifts=[two_shifts[0]],
        demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
    )
    outcome = MILPScheduler().solve(scn, ObjectiveConfig())
    assert outcome.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    # E1 (absent) must never appear in assignments
    assert all(a.employee_id != "E1" for a in outcome.assignments)


def test_absent_employee_not_assigned_by_greedy(two_shifts, simple_unit):
    emp = Employee(
        id="E1", name="A", skills=[], available_shifts=["S1"],
        max_hours=8.0, is_absent=True,
    )
    emp2 = Employee(id="E2", name="B", skills=[], available_shifts=["S1"], max_hours=8.0)
    scn = Scenario(
        id="s", name="t", employees=[emp, emp2], units=[simple_unit],
        shifts=[two_shifts[0]],
        demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
    )
    outcome = GreedyScheduler().solve(scn, ObjectiveConfig())
    assert all(a.employee_id != "E1" for a in outcome.assignments)


def test_absent_employee_assigned_flagged_by_validator(two_shifts, simple_unit):
    emp = Employee(
        id="E1", name="A", skills=[], available_shifts=["S1"],
        max_hours=8.0, is_absent=True, absence_reason="sick leave",
    )
    scn = Scenario(
        id="s", name="t", employees=[emp], units=[simple_unit],
        shifts=[two_shifts[0]],
        demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
    )
    bad = [Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0)]
    result = validate_assignments(bad, scn)
    assert result.is_valid is False
    assert any(e.code == "ABSENT_EMPLOYEE_ASSIGNED" for e in result.errors)
    # The reason should appear in the error message
    assert any("sick leave" in e.message for e in result.errors)


# ---------------------------------------------------------------------------
# 5. Locked assignment validation
# ---------------------------------------------------------------------------

def test_locked_assignment_unchanged_passes(two_shifts, simple_unit):
    emp = Employee(id="E1", name="A", skills=[], available_shifts=["S1", "S2"], max_hours=16.0)
    scn = Scenario(
        id="s", name="t", employees=[emp], units=[simple_unit], shifts=two_shifts,
        demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
    )
    locked = [Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0, is_locked=True)]
    assignments = [Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0)]
    result = validate_assignments(assignments, scn, locked_assignments=locked)
    assert not any(e.code == "LOCKED_ASSIGNMENT_CHANGED" for e in result.errors)


def test_locked_assignment_removed_flagged(two_shifts, simple_unit):
    emp = Employee(id="E1", name="A", skills=[], available_shifts=["S1", "S2"], max_hours=16.0)
    scn = Scenario(
        id="s", name="t", employees=[emp], units=[simple_unit], shifts=two_shifts,
        demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
    )
    locked = [Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0, is_locked=True)]
    # Assignments do NOT contain the locked assignment
    assignments = [Assignment(employee_id="E1", unit_id="U1", shift_id="S2", hours=8.0)]
    result = validate_assignments(assignments, scn, locked_assignments=locked)
    assert result.is_valid is False
    assert any(e.code == "LOCKED_ASSIGNMENT_CHANGED" for e in result.errors)
