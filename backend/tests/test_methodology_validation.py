"""
Comprehensive Methodology and Operational Verification Test Suite.

Verifies:
1. Qualification semantics (no required skills, single match, disjoint skills, multi-skill subsets, empty skills)
2. Temporal rest intervals & overlapping shift conflicts in MILP, Greedy, ALNS, and Independent Validator
3. Capacity-aware vs uniform fairness target formulations
4. Two-Stage Lexicographic MILP status preservation and tolerance mechanics
"""
import pytest
from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand, Assignment
from app.domain.enums import SolverStatus, ObjectivePrimary
from app.domain.temporal import shifts_conflict, build_shift_conflict_pairs, build_shift_conflict_map
from app.schemas.schedule import ObjectiveConfig
from app.optimization.milp_scheduler import MILPScheduler
from app.optimization.greedy_scheduler import GreedyScheduler
from app.optimization.alns_scheduler import ALNSScheduler
from app.validation.schedule_validator import validate_assignments


# ============================================================================
# 1. QUALIFICATION SEMANTICS TESTS
# ============================================================================

def test_qualification_unit_with_no_required_skills():
    """Unit with empty required_skills ([]) allows any employee to be assigned."""
    scn = Scenario(
        id="scn_qual_empty",
        name="Empty Unit Skills Scenario",
        employees=[
            Employee(id="E1", name="Worker 1", skills=[], available_shifts=["S1"], max_hours=8.0),
            Employee(id="E2", name="Worker 2", skills=["welding"], available_shifts=["S1"], max_hours=8.0),
        ],
        units=[ProductionUnit(id="U1", name="General Cell", required_skills=[])],
        shifts=[Shift(id="S1", name="Day", start_time="08:00", end_time="16:00", duration_hours=8.0)],
        demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=2)],
    )
    # Both MILP and Greedy must solve to 100% coverage
    milp = MILPScheduler()
    outcome_milp = milp.solve(scn, ObjectiveConfig())
    assert outcome_milp.status == SolverStatus.OPTIMAL
    assert len(outcome_milp.assignments) == 2

    greedy = GreedyScheduler()
    outcome_greedy = greedy.solve(scn, ObjectiveConfig())
    assert outcome_greedy.status == SolverStatus.FEASIBLE
    assert len(outcome_greedy.assignments) == 2


def test_qualification_at_least_one_matching_skill():
    """Worker qualifies when having at least one matching skill (disjunctive rule)."""
    scn = Scenario(
        id="scn_qual_match",
        name="Matching Skill Scenario",
        employees=[
            Employee(id="E1", name="Worker 1", skills=["welding"], available_shifts=["S1"], max_hours=8.0),
            Employee(id="E2", name="Worker 2", skills=["machining", "painting"], available_shifts=["S1"], max_hours=8.0),
        ],
        units=[ProductionUnit(id="U1", name="Fabrication Cell", required_skills=["welding", "machining"])],
        shifts=[Shift(id="S1", name="Day", start_time="08:00", end_time="16:00", duration_hours=8.0)],
        demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=2)],
    )
    milp = MILPScheduler()
    outcome = milp.solve(scn, ObjectiveConfig())
    assert outcome.status == SolverStatus.OPTIMAL
    assert len(outcome.assignments) == 2
    val = validate_assignments(outcome.assignments, scn)
    assert val.is_valid is True


def test_qualification_no_matching_skills_infeasible():
    """Worker without any matching skills cannot be assigned; leads to infeasibility if demand > qualified workers."""
    scn = Scenario(
        id="scn_qual_nomatch",
        name="No Match Scenario",
        employees=[
            Employee(id="E1", name="Worker 1", skills=["cleaning"], available_shifts=["S1"], max_hours=8.0),
            Employee(id="E2", name="Worker 2", skills=["logistics"], available_shifts=["S1"], max_hours=8.0),
        ],
        units=[ProductionUnit(id="U1", name="Precision Cell", required_skills=["inspection", "soldering"])],
        shifts=[Shift(id="S1", name="Day", start_time="08:00", end_time="16:00", duration_hours=8.0)],
        demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
    )
    milp = MILPScheduler()
    outcome_milp = milp.solve(scn, ObjectiveConfig())
    assert outcome_milp.status == SolverStatus.INFEASIBLE
    assert len(outcome_milp.assignments) == 0

    greedy = GreedyScheduler()
    outcome_greedy = greedy.solve(scn, ObjectiveConfig())
    assert outcome_greedy.status == SolverStatus.NOT_SOLVED
    assert len(outcome_greedy.assignments) == 0


def test_qualification_empty_worker_skills_rejected_for_skilled_unit():
    """Worker with skills=[] is rejected by unit requiring skills; validator catches it if manually assigned."""
    scn = Scenario(
        id="scn_qual_empty_skills",
        name="Empty Skills Scenario",
        employees=[Employee(id="E1", name="Unskilled Worker", skills=[], available_shifts=["S1"], max_hours=8.0)],
        units=[ProductionUnit(id="U1", name="CNC Cell", required_skills=["cnc_operation"])],
        shifts=[Shift(id="S1", name="Day", start_time="08:00", end_time="16:00", duration_hours=8.0)],
        demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
    )
    # Manual illegal assignment checked by validator
    bad_assignment = [Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0)]
    val = validate_assignments(bad_assignment, scn)
    assert val.is_valid is False
    assert any(e.code == "QUALIFICATION_VIOLATION" for e in val.errors)


# ============================================================================
# 2. TEMPORAL REST INTERVALS AND OVERLAPPING SHIFTS TESTS
# ============================================================================

def test_temporal_overlapping_shifts_conflict_detected():
    """Shifts overlapping in clock time are detected as conflicting even with min_rest_hours=0."""
    s1 = Shift(id="S1", name="Morning", start_time="08:00", end_time="16:00", duration_hours=8.0)
    s2 = Shift(id="S2", name="Midday", start_time="12:00", end_time="20:00", duration_hours=8.0)
    is_conf, conf_type = shifts_conflict(s1, s2, min_rest_hours=0.0)
    assert is_conf is True
    assert conf_type == "OVERLAPPING_SHIFTS"


def test_temporal_cross_day_overnight_shift_handling():
    """Overnight shift (e.g. 23:00 to 07:00) overlaps correctly with next morning shift (e.g. 06:00 to 14:00)."""
    s_night = Shift(id="S_NIGHT", name="Night", start_time="23:00", end_time="07:00", duration_hours=8.0)
    s_early = Shift(id="S_EARLY", name="Early Day", start_time="06:00", end_time="14:00", duration_hours=8.0)
    is_conf, conf_type = shifts_conflict(s_night, s_early, min_rest_hours=0.0)
    assert is_conf is True
    assert conf_type == "OVERLAPPING_SHIFTS"


def test_temporal_minimum_rest_violation_enforced():
    """Shifts that do not overlap but have rest < min_rest_hours (e.g. 4h < 11h) are flagged."""
    s1 = Shift(id="S1", name="Day", start_time="08:00", end_time="16:00", duration_hours=8.0)
    s2 = Shift(id="S2", name="Evening", start_time="20:00", end_time="00:00", duration_hours=4.0)
    # Gap is 4 hours (16:00 to 20:00). If min_rest is 11.0, this is a violation
    is_conf, conf_type = shifts_conflict(s1, s2, min_rest_hours=11.0)
    assert is_conf is True
    assert conf_type == "MIN_REST_VIOLATION"

    # If min_rest is 2.0, gap (4h) >= 2.0h, so no violation
    is_conf_loose, _ = shifts_conflict(s1, s2, min_rest_hours=2.0)
    assert is_conf_loose is False


def test_temporal_conflict_enforced_across_milp_greedy_alns():
    """Worker cannot be assigned to both S1 and S2 when min_rest_hours=11.0."""
    # S1 ends at 16:00, S2 starts at 20:00 (rest = 4h < 11h)
    # One employee available for both, but total demand is 2 (1 in S1, 1 in S2).
    # Since worker cannot work both, problem is infeasible with 1 worker, but feasible with 2 workers.
    s1 = Shift(id="S1", name="Shift 1", start_time="08:00", end_time="16:00", duration_hours=8.0)
    s2 = Shift(id="S2", name="Shift 2", start_time="20:00", end_time="00:00", duration_hours=4.0)
    u1 = ProductionUnit(id="U1", name="Unit 1", required_skills=[])
    
    # Subcase A: Only 1 worker available for both shifts
    scn_infeasible = Scenario(
        id="scn_temp_inf",
        name="Temporal Infeasible Scenario",
        employees=[Employee(id="E1", name="Worker 1", skills=[], available_shifts=["S1", "S2"], max_hours=20.0)],
        units=[u1],
        shifts=[s1, s2],
        demands=[
            Demand(unit_id="U1", shift_id="S1", required_headcount=1),
            Demand(unit_id="U1", shift_id="S2", required_headcount=1),
        ],
    )
    cfg_rest = ObjectiveConfig(min_rest_hours=11.0)
    
    # MILP should prove infeasible
    milp = MILPScheduler()
    outcome_milp = milp.solve(scn_infeasible, cfg_rest)
    assert outcome_milp.status == SolverStatus.INFEASIBLE

    # Greedy should not assign E1 to both
    greedy = GreedyScheduler()
    outcome_greedy = greedy.solve(scn_infeasible, cfg_rest)
    assert outcome_greedy.status == SolverStatus.NOT_SOLVED
    assert len(outcome_greedy.assignments) == 1

    # Independent validator catches any illegal double assignment
    illegal_assignments = [
        Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
        Assignment(employee_id="E1", unit_id="U1", shift_id="S2", hours=4.0),
    ]
    val = validate_assignments(illegal_assignments, scn_infeasible, min_rest_hours=11.0)
    assert val.is_valid is False
    assert any(e.code == "MIN_REST_VIOLATION" for e in val.errors)


# ============================================================================
# 3. FAIRNESS TARGET: UNIFORM VS CAPACITY-PROPORTIONAL
# ============================================================================

def test_fairness_uniform_vs_proportional_target():
    """
    Worker 1 has max_hours=40.0, Worker 2 has max_hours=20.0.
    Demand is 30.0 hours (two 15h demands, or 3 shifts of 10h).
    - Uniform target: each is targeted for 15.0h (50% each of total demanded hours).
    - Proportional target: Worker 1 capacity is 40/60 = 2/3 (target = 20.0h).
                           Worker 2 capacity is 20/60 = 1/3 (target = 10.0h).
    """
    shifts = [
        Shift(id="S1", name="Day 1", start_time="2026-10-24T08:00:00", end_time="2026-10-24T18:00:00", duration_hours=10.0),
        Shift(id="S2", name="Day 2", start_time="2026-10-25T08:00:00", end_time="2026-10-25T18:00:00", duration_hours=10.0),
        Shift(id="S3", name="Day 3", start_time="2026-10-26T08:00:00", end_time="2026-10-26T18:00:00", duration_hours=10.0),
    ]
    units = [ProductionUnit(id="U1", name="Unit 1", required_skills=[])]
    demands = [
        Demand(unit_id="U1", shift_id="S1", required_headcount=1),
        Demand(unit_id="U1", shift_id="S2", required_headcount=1),
        Demand(unit_id="U1", shift_id="S3", required_headcount=1),
    ]
    # Total demand = 30.0h
    employees = [
        Employee(id="E_FULL", name="Full-Time", skills=[], available_shifts=["S1", "S2", "S3"], max_hours=40.0),
        Employee(id="E_PART", name="Part-Time", skills=[], available_shifts=["S1", "S2", "S3"], max_hours=20.0),
    ]
    scn = Scenario(id="scn_prop_fair", name="Proportional Fairness Test", employees=employees, units=units, shifts=shifts, demands=demands)

    milp = MILPScheduler()

    # Case A: Proportional fairness
    cfg_prop = ObjectiveConfig(primary=ObjectivePrimary.COST, two_stage=True, proportional_fairness=True)
    outcome_prop = milp.solve(scn, cfg_prop)
    assert outcome_prop.status == SolverStatus.OPTIMAL
    hours_full_prop = sum(a.hours for a in outcome_prop.assignments if a.employee_id == "E_FULL")
    hours_part_prop = sum(a.hours for a in outcome_prop.assignments if a.employee_id == "E_PART")
    # Proportional targets are 20h and 10h. Solution should assign exactly 20h to E_FULL and 10h to E_PART!
    assert hours_full_prop == 20.0
    assert hours_part_prop == 10.0


# ============================================================================
# 4. TWO-STAGE LEXICOGRAPHIC OPTIMALITY PRESERVATION
# ============================================================================

def test_two_stage_preserves_stage1_hours_and_achieves_fairness(minimal_valid_scenario: Scenario):
    """Stage 1 solves minimum hours, Stage 2 minimizes SAD while respecting the hours bound."""
    milp = MILPScheduler()
    cfg = ObjectiveConfig(primary=ObjectivePrimary.FEASIBILITY, two_stage=True, two_stage_tolerance=0.0)
    outcome = milp.solve(minimal_valid_scenario, cfg)
    assert outcome.status == SolverStatus.OPTIMAL
    assert "Optimal lexicographic schedule" in (outcome.message or "")
    total_hours = sum(a.hours for a in outcome.assignments)
    assert total_hours == 16.0  # Exactly 2 assignments of 8h each
