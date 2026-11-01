"""
Tests for Manufacturing Routes & Replacement Services:
- Plant Policy retrieval
- Schedule Lifecycle transitions & approval gates
- Replacement candidate search and ranking
"""
import pytest
from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand
from app.domain.schedule_lifecycle import ScheduleLifecycleStatus
from app.domain.enums import QualificationPolicy
from app.services.replacement_service import find_replacement_candidates


def test_replacement_candidate_ranking():
    unit = ProductionUnit(
        id="U1", name="Machining", required_skills=["machining"],
        required_certifications=["safety_cert"]
    )
    shift = Shift(id="S1", name="Morning", start_time="08:00", end_time="16:00", duration_hours=8.0)

    # Worker 1: Qualified, consenting OT, no conflicts
    emp1 = Employee(
        id="E1", name="Alice", skills=["machining"], certifications=["safety_cert"],
        available_shifts=["S1"], max_hours=48.0, regular_hours_limit=40.0,
        overtime_opt_in=True, max_overtime_hours=8.0,
    )
    # Worker 2: Unqualified (missing certification)
    emp2 = Employee(
        id="E2", name="Bob", skills=["machining"], certifications=[],
        available_shifts=["S1"], max_hours=40.0,
    )
    # Worker 3: Absent
    emp3 = Employee(
        id="E3", name="Charlie", skills=["machining"], certifications=["safety_cert"],
        available_shifts=["S1"], max_hours=40.0, is_absent=True,
    )

    scenario = Scenario(
        id="s", name="test", employees=[emp1, emp2, emp3], units=[unit],
        shifts=[shift], demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)]
    )

    candidates = find_replacement_candidates(
        scenario=scenario,
        target_unit_id="U1",
        target_shift_id="S1",
        currently_assigned_hours={"E1": 32.0},
        assigned_shifts_by_emp={},
        qualification_policy=QualificationPolicy.LEVEL_AND_CERTIFICATION,
        min_rest_hours=11.0,
    )

    # Absent worker emp3 is skipped entirely
    emp_ids = [c.employee_id for c in candidates]
    assert "E3" not in emp_ids
    assert "E1" in emp_ids
    assert "E2" in emp_ids

    # E1 should be top-ranked candidate with positive suitability score
    assert candidates[0].employee_id == "E1"
    assert candidates[0].is_qualified is True
    assert candidates[0].suitability_score > 0

    # E2 is flagged unqualified
    e2_cand = next(c for c in candidates if c.employee_id == "E2")
    assert e2_cand.is_qualified is False
    assert "Lacks required" in (e2_cand.rejection_reason or "")
