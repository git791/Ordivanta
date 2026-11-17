from app.domain.models import Scenario, Demand, Assignment
from app.metrics.schedule_metrics import compute_metrics, compute_coverage


def test_compute_metrics_full_coverage(minimal_valid_scenario: Scenario):
    # minimal_valid_scenario has demand of 2 for (U1, S1)
    assignments = [
        Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
        Assignment(employee_id="E2", unit_id="U1", shift_id="S1", hours=8.0),
    ]

    metrics = compute_metrics(
        assignments=assignments,
        scenario=minimal_valid_scenario,
        runtime_seconds=0.123,
        objective_value=0.0,
        violation_count=0,
    )

    assert metrics.coverage_rate == 1.0
    assert metrics.unfilled_positions == 0
    assert metrics.total_required_positions == 2
    assert metrics.total_filled_positions == 2
    assert metrics.hard_constraint_violations == 0
    assert metrics.employee_hours == {"E1": 8.0, "E2": 8.0}
    assert metrics.workload_spread == 0.0  # stdev([8.0, 8.0]) is 0.0
    assert metrics.runtime_seconds == 0.123
    assert metrics.objective_value == 0.0

    filled, req, pct = compute_coverage(assignments, minimal_valid_scenario)
    assert filled == 2
    assert req == 2
    assert pct == 100.0


def test_compute_metrics_partial_coverage(minimal_valid_scenario: Scenario):
    # demand is 2, but only 1 assigned
    assignments = [
        Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
    ]

    metrics = compute_metrics(
        assignments=assignments,
        scenario=minimal_valid_scenario,
        runtime_seconds=0.05,
        objective_value=None,
        violation_count=0,
    )

    assert metrics.coverage_rate == 0.5
    assert metrics.unfilled_positions == 1
    assert metrics.total_required_positions == 2
    assert metrics.total_filled_positions == 1
    assert metrics.hard_constraint_violations == 0
    assert metrics.employee_hours == {"E1": 8.0}
    assert metrics.workload_spread is None  # only 1 employee has assignments

    filled, req, pct = compute_coverage(assignments, minimal_valid_scenario)
    assert filled == 1
    assert req == 2
    assert pct == 50.0


def test_compute_metrics_zero_demand(minimal_valid_scenario: Scenario):
    minimal_valid_scenario.demands = []
    assignments = []

    metrics = compute_metrics(
        assignments=assignments,
        scenario=minimal_valid_scenario,
        runtime_seconds=0.01,
        objective_value=0.0,
        violation_count=0,
    )

    assert metrics.coverage_rate == 1.0
    assert metrics.unfilled_positions == 0
    assert metrics.total_required_positions == 0
    assert metrics.total_filled_positions == 0
    assert metrics.workload_spread is None

    filled, req, pct = compute_coverage(assignments, minimal_valid_scenario)
    assert filled == 0
    assert req == 0
    assert pct == 100.0


def test_compute_coverage_overcoverage_capped_at_100():
    """Verify that assigning more workers than required in a cell caps coverage at 100% and cannot exceed 100%."""
    scenario = Scenario(
        id="scn_overcover",
        name="Overcoverage Scenario",
        demands=[
            Demand(unit_id="U1", shift_id="S1", required_headcount=2),
        ],
    )
    # Assign 5 workers to a cell that only requires 2
    assignments = [
        Assignment(employee_id=f"E{i}", unit_id="U1", shift_id="S1", hours=8.0)
        for i in range(1, 6)
    ]

    metrics = compute_metrics(
        assignments=assignments,
        scenario=scenario,
        runtime_seconds=0.02,
        objective_value=0.0,
        violation_count=0,
    )

    assert metrics.total_required_positions == 2
    assert metrics.total_filled_positions == 2
    assert metrics.unfilled_positions == 0
    assert metrics.coverage_rate == 1.0

    filled, req, pct = compute_coverage(assignments, scenario)
    assert filled == 2
    assert req == 2
    assert pct == 100.0
    assert pct <= 100.0


def test_compute_coverage_overcoverage_cannot_mask_shortfall():
    """Verify that surplus workers in one cell do NOT count toward covering deficits in another cell."""
    scenario = Scenario(
        id="scn_masking_test",
        name="Masking Scenario",
        demands=[
            Demand(unit_id="U1", shift_id="S1", required_headcount=2),
            Demand(unit_id="U2", shift_id="S1", required_headcount=2),
        ],
    )
    # Total required = 4.
    # 3 workers assigned to U1 (1 surplus)
    # 1 worker assigned to U2 (1 shortfall)
    # Total raw assignments = 4.
    assignments = [
        Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=8.0),
        Assignment(employee_id="E2", unit_id="U1", shift_id="S1", hours=8.0),
        Assignment(employee_id="E3", unit_id="U1", shift_id="S1", hours=8.0),
        Assignment(employee_id="E4", unit_id="U2", shift_id="S1", hours=8.0),
    ]

    metrics = compute_metrics(
        assignments=assignments,
        scenario=scenario,
        runtime_seconds=0.05,
        objective_value=None,
        violation_count=0,
    )

    # Fulfilled: min(3, 2) + min(1, 2) = 2 + 1 = 3 out of 4 (75%)
    assert metrics.total_required_positions == 4
    assert metrics.total_filled_positions == 3
    assert metrics.unfilled_positions == 1
    assert metrics.coverage_rate == 0.75

    filled, req, pct = compute_coverage(assignments, scenario)
    assert filled == 3
    assert req == 4
    assert pct == 75.0


def test_compute_metrics_workload_spread():
    scenario = Scenario(
        id="scn_spread",
        name="Spread Test",
        demands=[Demand(unit_id="U1", shift_id="S1", required_headcount=2)],
    )
    assignments = [
        Assignment(employee_id="E1", unit_id="U1", shift_id="S1", hours=10.0),
        Assignment(employee_id="E2", unit_id="U1", shift_id="S1", hours=4.0),
    ]
    metrics = compute_metrics(
        assignments=assignments,
        scenario=scenario,
        runtime_seconds=0.1,
        objective_value=None,
        violation_count=1,
    )

    assert metrics.hard_constraint_violations == 1
    assert metrics.employee_hours == {"E1": 10.0, "E2": 4.0}
    # stdev([10.0, 4.0]) is sqrt((6^2)/2) = 4.2426
    assert metrics.workload_spread is not None
    assert round(metrics.workload_spread, 2) == 4.24

