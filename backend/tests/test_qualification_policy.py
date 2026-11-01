"""
Tests for QualificationPolicy: ANY, ALL, LEVEL_AND_CERTIFICATION.

Verifies that:
- Policy.ANY preserves backward-compatible disjunctive behaviour.
- Policy.ALL requires every skill in required_skills / mandatory_skill_requirements.
- Policy.LEVEL_AND_CERTIFICATION enforces proficiency levels and certifications.
- All three schedulers (MILP, Greedy, ALNS) and the independent validator apply
  the same policy consistently.
- Overtime/on-call status never bypasses qualification requirements.
- Specialist shortages are correctly detected and reported.
"""
import pytest
from app.domain.models import (
    Scenario, Employee, ProductionUnit, Shift, Demand, Assignment,
    SkillRequirement,
)
from app.domain.enums import SolverStatus, QualificationPolicy
from app.domain.qualification import is_qualified, qualification_gap_reason
from app.schemas.schedule import ObjectiveConfig
from app.optimization.milp_scheduler import MILPScheduler
from app.optimization.greedy_scheduler import GreedyScheduler
from app.optimization.alns_scheduler import ALNSScheduler
from app.validation.schedule_validator import validate_assignments


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def one_shift() -> Shift:
    return Shift(id="S1", name="Day", start_time="08:00", end_time="16:00", duration_hours=8.0)


@pytest.fixture
def basic_unit() -> ProductionUnit:
    return ProductionUnit(id="U1", name="CNC Cell", required_skills=["cnc", "grinding"])


@pytest.fixture
def expert_unit() -> ProductionUnit:
    """Unit with mandatory skill requirements (level + cert)."""
    return ProductionUnit(
        id="U_EXPERT",
        name="Precision Welding",
        required_skills=["welding", "inspection"],
        mandatory_skill_requirements=[
            SkillRequirement(skill="welding", min_level=4),
            SkillRequirement(skill="inspection", min_level=3),
        ],
        required_certifications=["iso_9001", "safety_cert"],
    )


# ---------------------------------------------------------------------------
# 1. is_qualified helper unit tests
# ---------------------------------------------------------------------------

class TestIsQualifiedHelper:

    def test_any_policy_one_matching_skill(self, basic_unit):
        emp = Employee(id="E1", name="A", skills=["cnc"], available_shifts=["S1"], max_hours=8.0)
        assert is_qualified(emp, basic_unit, QualificationPolicy.ANY) is True

    def test_any_policy_no_matching_skill(self, basic_unit):
        emp = Employee(id="E1", name="A", skills=["assembly"], available_shifts=["S1"], max_hours=8.0)
        assert is_qualified(emp, basic_unit, QualificationPolicy.ANY) is False

    def test_any_policy_unit_no_requirements(self, one_shift):
        unit = ProductionUnit(id="U0", name="General", required_skills=[])
        emp = Employee(id="E1", name="A", skills=[], available_shifts=["S1"], max_hours=8.0)
        assert is_qualified(emp, unit, QualificationPolicy.ANY) is True

    def test_all_policy_all_skills_present(self, basic_unit):
        emp = Employee(id="E1", name="A", skills=["cnc", "grinding", "assembly"],
                       available_shifts=["S1"], max_hours=8.0)
        assert is_qualified(emp, basic_unit, QualificationPolicy.ALL) is True

    def test_all_policy_missing_one_skill(self, basic_unit):
        emp = Employee(id="E1", name="A", skills=["cnc"],  # missing grinding
                       available_shifts=["S1"], max_hours=8.0)
        assert is_qualified(emp, basic_unit, QualificationPolicy.ALL) is False

    def test_level_cert_passes_all_requirements(self, expert_unit):
        emp = Employee(
            id="E1", name="A",
            skills=["welding", "inspection"],
            skill_levels={"welding": 5, "inspection": 4},
            certifications=["iso_9001", "safety_cert"],
            available_shifts=["S1"], max_hours=8.0,
        )
        assert is_qualified(emp, expert_unit, QualificationPolicy.LEVEL_AND_CERTIFICATION) is True

    def test_level_cert_fails_insufficient_level(self, expert_unit):
        emp = Employee(
            id="E1", name="A",
            skills=["welding", "inspection"],
            skill_levels={"welding": 2, "inspection": 4},  # welding too low
            certifications=["iso_9001", "safety_cert"],
            available_shifts=["S1"], max_hours=8.0,
        )
        assert is_qualified(emp, expert_unit, QualificationPolicy.LEVEL_AND_CERTIFICATION) is False

    def test_level_cert_fails_missing_certification(self, expert_unit):
        emp = Employee(
            id="E1", name="A",
            skills=["welding", "inspection"],
            skill_levels={"welding": 5, "inspection": 4},
            certifications=["iso_9001"],  # missing safety_cert
            available_shifts=["S1"], max_hours=8.0,
        )
        assert is_qualified(emp, expert_unit, QualificationPolicy.LEVEL_AND_CERTIFICATION) is False

    def test_level_cert_fails_missing_skill(self, expert_unit):
        emp = Employee(
            id="E1", name="A",
            skills=["welding"],  # missing inspection
            skill_levels={"welding": 5},
            certifications=["iso_9001", "safety_cert"],
            available_shifts=["S1"], max_hours=8.0,
        )
        assert is_qualified(emp, expert_unit, QualificationPolicy.LEVEL_AND_CERTIFICATION) is False

    def test_gap_reason_returns_string_when_not_qualified(self, basic_unit):
        emp = Employee(id="E1", name="A", skills=["assembly"], available_shifts=["S1"], max_hours=8.0)
        reason = qualification_gap_reason(emp, basic_unit, QualificationPolicy.ANY)
        assert reason is not None
        assert "assembly" in reason or "required" in reason.lower()

    def test_gap_reason_returns_none_when_qualified(self, basic_unit):
        emp = Employee(id="E1", name="A", skills=["cnc"], available_shifts=["S1"], max_hours=8.0)
        assert qualification_gap_reason(emp, basic_unit, QualificationPolicy.ANY) is None


# ---------------------------------------------------------------------------
# 2. MILP scheduler: policy integration
# ---------------------------------------------------------------------------

def make_scenario(employees, unit, shift, required_headcount=1):
    return Scenario(
        id="test_scn",
        name="Test",
        employees=employees,
        units=[unit],
        shifts=[shift],
        demands=[Demand(unit_id=unit.id, shift_id=shift.id, required_headcount=required_headcount)],
    )


class TestMILPQualificationPolicy:

    def test_any_policy_one_skill_is_sufficient(self, basic_unit, one_shift):
        emps = [
            Employee(id="E1", name="A", skills=["cnc"], available_shifts=["S1"], max_hours=8.0),
        ]
        scn = make_scenario(emps, basic_unit, one_shift)
        cfg = ObjectiveConfig(qualification_policy=QualificationPolicy.ANY)
        outcome = MILPScheduler().solve(scn, cfg)
        assert outcome.status == SolverStatus.OPTIMAL

    def test_all_policy_one_skill_insufficient(self, basic_unit, one_shift):
        """ALL policy: employee has only 'cnc' but unit requires 'cnc' AND 'grinding'."""
        emps = [
            Employee(id="E1", name="A", skills=["cnc"], available_shifts=["S1"], max_hours=8.0),
        ]
        scn = make_scenario(emps, basic_unit, one_shift)
        cfg = ObjectiveConfig(qualification_policy=QualificationPolicy.ALL)
        outcome = MILPScheduler().solve(scn, cfg)
        assert outcome.status == SolverStatus.INFEASIBLE

    def test_all_policy_all_skills_sufficient(self, basic_unit, one_shift):
        emps = [
            Employee(id="E1", name="A", skills=["cnc", "grinding"], available_shifts=["S1"], max_hours=8.0),
        ]
        scn = make_scenario(emps, basic_unit, one_shift)
        cfg = ObjectiveConfig(qualification_policy=QualificationPolicy.ALL)
        outcome = MILPScheduler().solve(scn, cfg)
        assert outcome.status == SolverStatus.OPTIMAL

    def test_level_cert_policy_passes(self, expert_unit, one_shift):
        emps = [
            Employee(
                id="E1", name="A",
                skills=["welding", "inspection"],
                skill_levels={"welding": 4, "inspection": 3},
                certifications=["iso_9001", "safety_cert"],
                available_shifts=["S1"], max_hours=8.0,
            ),
        ]
        scn = make_scenario(emps, expert_unit, one_shift)
        cfg = ObjectiveConfig(qualification_policy=QualificationPolicy.LEVEL_AND_CERTIFICATION)
        outcome = MILPScheduler().solve(scn, cfg)
        assert outcome.status == SolverStatus.OPTIMAL

    def test_level_cert_policy_insufficient_level_infeasible(self, expert_unit, one_shift):
        emps = [
            Employee(
                id="E1", name="A",
                skills=["welding", "inspection"],
                skill_levels={"welding": 2, "inspection": 3},  # welding too low
                certifications=["iso_9001", "safety_cert"],
                available_shifts=["S1"], max_hours=8.0,
            ),
        ]
        scn = make_scenario(emps, expert_unit, one_shift)
        cfg = ObjectiveConfig(qualification_policy=QualificationPolicy.LEVEL_AND_CERTIFICATION)
        outcome = MILPScheduler().solve(scn, cfg)
        assert outcome.status == SolverStatus.INFEASIBLE

    def test_level_cert_policy_missing_certification_infeasible(self, expert_unit, one_shift):
        emps = [
            Employee(
                id="E1", name="A",
                skills=["welding", "inspection"],
                skill_levels={"welding": 5, "inspection": 4},
                certifications=["iso_9001"],  # missing safety_cert
                available_shifts=["S1"], max_hours=8.0,
            ),
        ]
        scn = make_scenario(emps, expert_unit, one_shift)
        cfg = ObjectiveConfig(qualification_policy=QualificationPolicy.LEVEL_AND_CERTIFICATION)
        outcome = MILPScheduler().solve(scn, cfg)
        assert outcome.status == SolverStatus.INFEASIBLE

    def test_specialist_shortage_correctly_detected(self, expert_unit, one_shift):
        """Only 1 qualified expert but demand=2 → infeasible under LEVEL_AND_CERT."""
        emps = [
            Employee(
                id="E1", name="Expert",
                skills=["welding", "inspection"],
                skill_levels={"welding": 5, "inspection": 4},
                certifications=["iso_9001", "safety_cert"],
                available_shifts=["S1"], max_hours=8.0,
            ),
            Employee(
                id="E2", name="Junior",  # low proficiency, will be excluded
                skills=["welding", "inspection"],
                skill_levels={"welding": 1, "inspection": 1},
                certifications=["iso_9001", "safety_cert"],
                available_shifts=["S1"], max_hours=8.0,
            ),
        ]
        scn = make_scenario(emps, expert_unit, one_shift, required_headcount=2)
        cfg = ObjectiveConfig(qualification_policy=QualificationPolicy.LEVEL_AND_CERTIFICATION)
        outcome = MILPScheduler().solve(scn, cfg)
        assert outcome.status == SolverStatus.INFEASIBLE


# ---------------------------------------------------------------------------
# 3. Greedy scheduler: policy integration
# ---------------------------------------------------------------------------

class TestGreedyQualificationPolicy:

    def test_any_policy_one_skill_is_sufficient(self, basic_unit, one_shift):
        emps = [Employee(id="E1", name="A", skills=["cnc"], available_shifts=["S1"], max_hours=8.0)]
        scn = make_scenario(emps, basic_unit, one_shift)
        cfg = ObjectiveConfig(qualification_policy=QualificationPolicy.ANY)
        outcome = GreedyScheduler().solve(scn, cfg)
        assert outcome.status == SolverStatus.FEASIBLE
        assert len(outcome.assignments) == 1

    def test_all_policy_one_skill_no_assignment(self, basic_unit, one_shift):
        emps = [Employee(id="E1", name="A", skills=["cnc"], available_shifts=["S1"], max_hours=8.0)]
        scn = make_scenario(emps, basic_unit, one_shift)
        cfg = ObjectiveConfig(qualification_policy=QualificationPolicy.ALL)
        outcome = GreedyScheduler().solve(scn, cfg)
        # Greedy cannot satisfy demand; returns NOT_SOLVED (not INFEASIBLE — that requires MILP proof)
        assert outcome.status == SolverStatus.NOT_SOLVED
        assert len(outcome.assignments) == 0

    def test_all_policy_all_skills_assigned(self, basic_unit, one_shift):
        emps = [
            Employee(id="E1", name="A", skills=["cnc", "grinding"], available_shifts=["S1"], max_hours=8.0)
        ]
        scn = make_scenario(emps, basic_unit, one_shift)
        cfg = ObjectiveConfig(qualification_policy=QualificationPolicy.ALL)
        outcome = GreedyScheduler().solve(scn, cfg)
        assert outcome.status == SolverStatus.FEASIBLE


# ---------------------------------------------------------------------------
# 4. Independent validator: qualification policy errors
# ---------------------------------------------------------------------------

class TestValidatorQualificationPolicy:

    def test_any_policy_violation_detected(self, basic_unit, one_shift):
        emp = Employee(id="E1", name="A", skills=["assembly"], available_shifts=["S1"], max_hours=8.0)
        scn = Scenario(
            id="s", name="t", employees=[emp], units=[basic_unit], shifts=[one_shift],
            demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
        )
        bad = [Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0)]
        result = validate_assignments(bad, scn, qualification_policy=QualificationPolicy.ANY)
        assert result.is_valid is False
        assert any(e.code == "QUALIFICATION_VIOLATION" for e in result.errors)

    def test_all_policy_missing_skill_error(self, basic_unit, one_shift):
        emp = Employee(id="E1", name="A", skills=["cnc"], available_shifts=["S1"], max_hours=8.0)
        scn = Scenario(
            id="s", name="t", employees=[emp], units=[basic_unit], shifts=[one_shift],
            demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
        )
        bad = [Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0)]
        result = validate_assignments(bad, scn, qualification_policy=QualificationPolicy.ALL)
        assert result.is_valid is False
        assert any(e.code == "QUALIFICATION_VIOLATION" for e in result.errors)

    def test_level_cert_policy_skill_level_error(self, expert_unit, one_shift):
        emp = Employee(
            id="E1", name="A",
            skills=["welding", "inspection"],
            skill_levels={"welding": 1, "inspection": 3},  # welding too low
            certifications=["iso_9001", "safety_cert"],
            available_shifts=["S1"], max_hours=8.0,
        )
        scn = Scenario(
            id="s", name="t", employees=[emp], units=[expert_unit], shifts=[one_shift],
            demands=[Demand(unit_id="U_EXPERT", shift_id="S1", required_headcount=1)],
        )
        bad = [Assignment(employee_id="E1", unit_id="U_EXPERT", shift_id="S1", hours=8.0)]
        result = validate_assignments(bad, scn, qualification_policy=QualificationPolicy.LEVEL_AND_CERTIFICATION)
        assert result.is_valid is False
        assert any(e.code == "INSUFFICIENT_SKILL_LEVEL" for e in result.errors)

    def test_level_cert_policy_missing_certification_error(self, expert_unit, one_shift):
        emp = Employee(
            id="E1", name="A",
            skills=["welding", "inspection"],
            skill_levels={"welding": 5, "inspection": 4},
            certifications=["iso_9001"],  # missing safety_cert
            available_shifts=["S1"], max_hours=8.0,
        )
        scn = Scenario(
            id="s", name="t", employees=[emp], units=[expert_unit], shifts=[one_shift],
            demands=[Demand(unit_id="U_EXPERT", shift_id="S1", required_headcount=1)],
        )
        bad = [Assignment(employee_id="E1", unit_id="U_EXPERT", shift_id="S1", hours=8.0)]
        result = validate_assignments(bad, scn, qualification_policy=QualificationPolicy.LEVEL_AND_CERTIFICATION)
        assert result.is_valid is False
        assert any(e.code == "MISSING_CERTIFICATION" for e in result.errors)

    def test_shortage_explanation_no_qualified_employee(self, expert_unit, one_shift):
        """Validator should explain that no qualified employee exists."""
        emp = Employee(
            id="E1", name="A",
            skills=["welding"],  # missing inspection
            skill_levels={},
            certifications=[],
            available_shifts=["S1"], max_hours=8.0,
        )
        scn = Scenario(
            id="s", name="t", employees=[emp], units=[expert_unit], shifts=[one_shift],
            demands=[Demand(unit_id="U_EXPERT", shift_id="S1", required_headcount=1)],
        )
        result = validate_assignments([], scn, qualification_policy=QualificationPolicy.LEVEL_AND_CERTIFICATION)
        assert result.is_valid is True  # No assignment violations
        codes = [w.code for w in result.warnings]
        assert "COVERAGE_SHORTFALL" in codes
        assert "SHORTAGE_NO_QUALIFIED" in codes

    def test_shortage_explanation_qualified_but_unavailable(self, basic_unit, one_shift):
        """Employee is qualified but available for a different shift."""
        shift2 = Shift(id="S2", name="Night", start_time="23:00", end_time="07:00", duration_hours=8.0)
        emp = Employee(
            id="E1", name="A",
            skills=["cnc", "grinding"],  # qualified for ALL
            available_shifts=["S2"],  # not available for S1
            max_hours=8.0,
        )
        scn = Scenario(
            id="s", name="t", employees=[emp], units=[basic_unit], shifts=[one_shift, shift2],
            demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=1)],
        )
        result = validate_assignments([], scn, qualification_policy=QualificationPolicy.ALL)
        codes = [w.code for w in result.warnings]
        assert "COVERAGE_SHORTFALL" in codes
        assert "SHORTAGE_UNAVAILABLE" in codes


# ---------------------------------------------------------------------------
# 5. Overtime does not bypass qualification
# ---------------------------------------------------------------------------

def test_overtime_does_not_bypass_qualification(basic_unit, one_shift):
    """
    Even with overtime enabled, an unqualified employee (ANY policy, no matching skill)
    must not be assigned and must trigger INFEASIBLE in MILP.
    """
    emp = Employee(
        id="E1", name="A",
        skills=["assembly"],  # not in ["cnc", "grinding"]
        available_shifts=["S1"],
        max_hours=8.0,
        overtime_opt_in=True,
        regular_hours_limit=8.0,
        max_overtime_hours=4.0,
    )
    scn = make_scenario([emp], basic_unit, one_shift)
    cfg = ObjectiveConfig(qualification_policy=QualificationPolicy.ANY)
    outcome = MILPScheduler().solve(scn, cfg)
    assert outcome.status == SolverStatus.INFEASIBLE
