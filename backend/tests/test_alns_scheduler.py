import pytest
from app.domain.models import Scenario
from app.domain.enums import SolverStatus
from app.schemas.schedule import ObjectiveConfig
from app.optimization.alns_scheduler import ALNSScheduler
from app.validation.schedule_validator import validate_assignments


def test_alns_solves_feasible_small(minimal_valid_scenario: Scenario):
    scheduler = ALNSScheduler(max_iterations=50, seed=42)
    outcome = scheduler.solve(minimal_valid_scenario, ObjectiveConfig())

    assert outcome.status == SolverStatus.FEASIBLE
    assert len(outcome.assignments) == 2
    assert outcome.objective_value is not None
    assert outcome.runtime_seconds >= 0.0

    # Independent validation
    val = validate_assignments(outcome.assignments, minimal_valid_scenario)
    assert val.is_valid is True
    assert len(val.errors) == 0


def test_alns_respects_infeasible_scenario(infeasible_scenario: Scenario):
    scheduler = ALNSScheduler(max_iterations=30, seed=42)
    outcome = scheduler.solve(infeasible_scenario, ObjectiveConfig())

    # Heuristic ALNS reports NOT_SOLVED on shortages, never claiming mathematical INFEASIBLE or FEASIBLE
    assert outcome.status == SolverStatus.NOT_SOLVED
    val = validate_assignments(outcome.assignments, infeasible_scenario)
    # Any partial assignments still must not violate availability or max hours
    assert len(val.errors) == 0
