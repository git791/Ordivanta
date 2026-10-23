import pytest
from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand, Assignment
from app.domain.enums import SolverStatus
from app.schemas.schedule import ObjectiveConfig
from app.optimization.milp_scheduler import MILPScheduler
from app.optimization.solver_adapter import get_solver
from app.optimization.base import SolverUnavailableError
from app.validation.schedule_validator import validate_assignments


def solver_available() -> bool:
    try:
        s = get_solver()
        return bool(s.available()) if hasattr(s, "available") else True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not solver_available(),
    reason="MILP solver (HiGHS/CBC) is not available in current environment",
)


# 1. Fully feasible small scenario
def test_scenario_1_fully_feasible_small(minimal_valid_scenario: Scenario):
    scheduler = MILPScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.OPTIMAL
    assert len(outcome.assignments) == 2
    val = validate_assignments(outcome.assignments, minimal_valid_scenario)
    assert val.is_valid is True


# 2. Demand greater than qualified available workforce
def test_scenario_2_demand_greater_than_workforce(infeasible_scenario: Scenario):
    scheduler = MILPScheduler()
    outcome = scheduler.solve(infeasible_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.INFEASIBLE
    assert len(outcome.assignments) == 0


# 3. Employee unavailable for a requested shift
def test_scenario_3_unavailable_for_shift(minimal_valid_scenario: Scenario):
    # Only E1 is available, but demand is 2
    minimal_valid_scenario.employees[1].available_shifts = []
    minimal_valid_scenario.employees[2].available_shifts = []
    scheduler = MILPScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.INFEASIBLE


# 4. Employee missing unit qualification
def test_scenario_4_missing_unit_qualification(minimal_valid_scenario: Scenario):
    # Only E1 has required skill, demand is 2
    minimal_valid_scenario.employees[1].skills = ["other_skill"]
    minimal_valid_scenario.employees[2].skills = ["other_skill"]
    scheduler = MILPScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.INFEASIBLE


# 5. Duplicate assignment prevention in one shift
def test_scenario_5_duplicate_assignment_prevented(minimal_valid_scenario: Scenario):
    # Add a second unit with demand=1 in S1.
    # Total demand in S1 is 3 (2 for U1, 1 for U2).
    # We have 3 employees, so each should work at most 1 unit in S1.
    minimal_valid_scenario.units.append(
        ProductionUnit(id="U2", name="Unit 2", required_skills=["assembly"])
    )
    minimal_valid_scenario.demands.append(
        Demand(unit_id="U2", shift_id="S1", required_headcount=1)
    )
    scheduler = MILPScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.OPTIMAL
    assert len(outcome.assignments) == 3
    # Validate no duplicate assignments
    emp_shifts = [a.employee_id for a in outcome.assignments]
    assert len(emp_shifts) == len(set(emp_shifts))


# 6. Total assigned hours above maximum prevented
def test_scenario_6_hours_limit_enforced(minimal_valid_scenario: Scenario):
    # Add S2 with demand=2. Total demand across S1 and S2 is 4 (2 in S1, 2 in S2).
    # All employees have max_hours=8.0 and shift duration=8.0.
    # 3 employees * 8h = 24h capacity. Demand needs 4 * 8h = 32h!
    minimal_valid_scenario.shifts.append(
        Shift(
            id="S2",
            name="Night Shift",
            start_time="16:00",
            end_time="00:00",
            duration_hours=8.0,
        )
    )
    for emp in minimal_valid_scenario.employees:
        emp.available_shifts.append("S2")

    minimal_valid_scenario.demands.append(
        Demand(unit_id="U1", shift_id="S2", required_headcount=2)
    )
    scheduler = MILPScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.INFEASIBLE


# 7. Zero-demand scenario
def test_scenario_7_zero_demand(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.demands = []
    scheduler = MILPScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.OPTIMAL
    assert len(outcome.assignments) == 0


# 8. Solver timeout or missing solver
def test_scenario_8_missing_solver():
    with pytest.raises(SolverUnavailableError):
        get_solver(name="INVALID_SOLVER_NAME")


# 9. Tampered extracted assignment caught by independent validator
def test_scenario_9_tampered_assignment_caught(minimal_valid_scenario: Scenario):
    scheduler = MILPScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.OPTIMAL

    # Tamper with an extracted assignment
    tampered = list(outcome.assignments)
    tampered.append(
        Assignment(
            employee_id=minimal_valid_scenario.employees[0].id,
            unit_id=minimal_valid_scenario.units[0].id,
            shift_id="INVALID_SHIFT_ID",
            hours=8.0,
        )
    )
    val = validate_assignments(tampered, minimal_valid_scenario)
    assert val.is_valid is False
    assert any(e.code == "AVAILABILITY_VIOLATION" for e in val.errors)
