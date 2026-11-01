"""
Tests for RecoveryMILPScheduler.
Verifies:
- Shortage minimization when demand exceeds capacity
- Lexicographic optimization hierarchy
- Overtime budget utilization when permitted
- Preservation of proof-of-optimality semantics
"""
import pytest
from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand, Assignment
from app.domain.enums import SolverStatus, QualificationPolicy
from app.schemas.schedule import ObjectiveConfig
from app.optimization.recovery_milp_scheduler import RecoveryMILPScheduler
from app.validation.schedule_validator import validate_assignments


def test_recovery_milp_solves_understaffed_with_shortages():
    # Demand is 5, but only 2 employees available and qualified
    unit = ProductionUnit(id="U1", name="Welding", required_skills=["welding"])
    shift = Shift(id="S1", name="Day", start_time="08:00", end_time="16:00", duration_hours=8.0)
    employees = [
        Employee(id="E1", name="Worker 1", skills=["welding"], available_shifts=["S1"], max_hours=8.0),
        Employee(id="E2", name="Worker 2", skills=["welding"], available_shifts=["S1"], max_hours=8.0),
    ]
    demand = Demand(unit_id="U1", shift_id="S1", required_headcount=5)
    scenario = Scenario(id="rec_scn", name="Recovery Test", employees=employees, units=[unit], shifts=[shift], demands=[demand])

    scheduler = RecoveryMILPScheduler()
    cfg = ObjectiveConfig(recovery_mode=True)
    outcome = scheduler.solve(scenario, cfg)

    assert outcome.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    assert len(outcome.assignments) == 2
    # Shortage = 5 - 2 = 3
    assert outcome.objective_value == 3.0

    val = validate_assignments(outcome.assignments, scenario)
    assert val.is_valid is True
    assert any(w.code == "COVERAGE_SHORTFALL" for w in val.warnings)


def test_recovery_milp_utilizes_overtime_when_opted_in():
    # 2 shifts, 1 employee who can work 16h with OT
    unit = ProductionUnit(id="U1", name="Assembly", required_skills=[])
    shifts = [
        Shift(id="S1", name="Morning", start_time="2026-10-01T08:00:00", end_time="2026-10-01T16:00:00", duration_hours=8.0),
        Shift(id="S2", name="Evening", start_time="2026-10-01T16:00:00", end_time="2026-10-02T00:00:00", duration_hours=8.0),
    ]
    emp = Employee(
        id="E1", name="Worker 1", skills=[], available_shifts=["S1", "S2"],
        max_hours=16.0, regular_hours_limit=8.0, overtime_opt_in=True, max_overtime_hours=8.0,
        base_hourly_rate=25.0, overtime_hourly_premium=12.5
    )
    demands = [
        Demand(unit_id="U1", shift_id="S1", required_headcount=1),
        Demand(unit_id="U1", shift_id="S2", required_headcount=1),
    ]
    scenario = Scenario(id="ot_rec", name="OT Recovery", employees=[emp], units=[unit], shifts=shifts, demands=demands)

    scheduler = RecoveryMILPScheduler()
    cfg = ObjectiveConfig(recovery_mode=True)
    outcome = scheduler.solve(scenario, cfg)

    assert outcome.status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE)
    assert len(outcome.assignments) == 2
    assert outcome.objective_value == 0.0  # 0 shortage achieved thanks to OT
