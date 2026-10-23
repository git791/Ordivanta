from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand, Assignment
from app.domain.enums import SolverStatus
from app.schemas.schedule import ObjectiveConfig
from app.optimization.greedy_scheduler import GreedyScheduler
from app.validation.schedule_validator import validate_assignments


# 1. Fully feasible small scenario
def test_greedy_scenario_1_fully_feasible_small(minimal_valid_scenario: Scenario):
    scheduler = GreedyScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    # Greedy NEVER claims OPTIMAL, must return FEASIBLE
    assert outcome.status == SolverStatus.FEASIBLE
    assert len(outcome.assignments) == 2
    val = validate_assignments(outcome.assignments, minimal_valid_scenario)
    assert val.is_valid is True


# 2. Demand greater than qualified available workforce
def test_greedy_scenario_2_demand_greater_than_workforce(infeasible_scenario: Scenario):
    scheduler = GreedyScheduler()
    outcome = scheduler.solve(infeasible_scenario, ObjectiveConfig())
    # Greedy returns NOT_SOLVED (partial schedule with shortages) rather than claiming mathematical INFEASIBLE
    assert outcome.status == SolverStatus.NOT_SOLVED


# 3. Employee unavailable for a requested shift
def test_greedy_scenario_3_unavailable_for_shift(minimal_valid_scenario: Scenario):
    # Only E1 is available, demand is 2
    minimal_valid_scenario.employees[1].available_shifts = []
    minimal_valid_scenario.employees[2].available_shifts = []
    scheduler = GreedyScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.NOT_SOLVED


# 4. Employee missing unit qualification
def test_greedy_scenario_4_missing_unit_qualification(minimal_valid_scenario: Scenario):
    # Only E1 has required skill, demand is 2
    minimal_valid_scenario.employees[1].skills = ["other_skill"]
    minimal_valid_scenario.employees[2].skills = ["other_skill"]
    scheduler = GreedyScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.NOT_SOLVED


# 5. Duplicate assignment prevented in one shift
def test_greedy_scenario_5_duplicate_assignment_prevented(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.units.append(
        ProductionUnit(id="U2", name="Unit 2", required_skills=["assembly"])
    )
    minimal_valid_scenario.demands.append(
        Demand(unit_id="U2", shift_id="S1", required_headcount=1)
    )
    scheduler = GreedyScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.FEASIBLE
    assert len(outcome.assignments) == 3
    # Check that no employee is assigned twice to S1
    emp_ids = [a.employee_id for a in outcome.assignments]
    assert len(emp_ids) == len(set(emp_ids))


# 6. Total assigned hours above maximum prevented
def test_greedy_scenario_6_hours_limit_enforced(minimal_valid_scenario: Scenario):
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
    scheduler = GreedyScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    # Capacity is 24h, demand is 32h -> NOT_SOLVED (shortages exist)
    assert outcome.status == SolverStatus.NOT_SOLVED
    # Ensure no employee had their hours exceeded
    for emp in minimal_valid_scenario.employees:
        total_hours = sum(a.hours for a in outcome.assignments if a.employee_id == emp.id)
        assert total_hours <= emp.max_hours


# 7. Zero-demand scenario
def test_greedy_scenario_7_zero_demand(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.demands = []
    scheduler = GreedyScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.FEASIBLE
    assert len(outcome.assignments) == 0


# 8. Deterministic behaviour on fixed inputs
def test_greedy_scenario_8_deterministic(minimal_valid_scenario: Scenario):
    scheduler = GreedyScheduler()
    outcome1 = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    outcome2 = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert [(a.employee_id, a.unit_id, a.shift_id) for a in outcome1.assignments] == [
        (a.employee_id, a.unit_id, a.shift_id) for a in outcome2.assignments
    ]


# 9. Tampered extracted assignment caught by independent validator
def test_greedy_scenario_9_tampered_assignment_caught(minimal_valid_scenario: Scenario):
    scheduler = GreedyScheduler()
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())
    assert outcome.status == SolverStatus.FEASIBLE

    tampered = list(outcome.assignments)
    tampered.append(
        Assignment(
            employee_id=minimal_valid_scenario.employees[0].id,
            unit_id=minimal_valid_scenario.units[0].id,
            shift_id="NON_EXISTENT_SHIFT",
            hours=8.0,
        )
    )
    val = validate_assignments(tampered, minimal_valid_scenario)
    assert val.is_valid is False
    assert any(e.code == "AVAILABILITY_VIOLATION" for e in val.errors)
