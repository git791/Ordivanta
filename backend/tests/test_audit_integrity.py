"""
Academic Audit & Reproducibility Integrity Tests for Ordivanta.
Verifies:
1. Truthful dataset instance counts matching disk files.
2. Full vs reduced dataset loading integrity.
3. Temporal non-overlap interval validator enforcement.
4. Absence of fabricated timeouts in benchmark scripts.
5. Absence of hardcoded figures in artifact generation.
6. Legitimate resource limit handling and incumbent preservation.
7. Fair disruption recovery baseline verification.
"""

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
DATA_DIR = ROOT / "data"
BENCH_DIR = DATA_DIR / "benchmark_results"


def test_manifest_matches_actual_disk_files():
    manifest_path = DATA_DIR / "dataset_manifest.json"
    assert manifest_path.exists(), "dataset_manifest.json must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    ds_map = {d["dataset_id"]: d for d in manifest["datasets"]}

    # MATSP
    matsp_files = list((DATA_DIR / "instances1_225" / "instances1_225" / "txt").glob("*.txt"))
    assert len(matsp_files) == 225
    assert ds_map["shift_scheduling"]["total_benchmark_instances"] == 225

    # PTSP
    ptsp_files = list((DATA_DIR / "ptask" / "ptsp").glob("*.dat"))
    assert len(ptsp_files) == 137
    assert ds_map["ptsp"]["total_benchmark_instances"] == 137
    assert ds_map["ptsp"]["worker_pool_max"] == 422
    assert ds_map["ptsp"]["task_count_max"] == 2105

    # SMPTSP
    smptsp_files = list((DATA_DIR / "smptsp" / "instances").glob("*.dat"))
    assert len(smptsp_files) == 10
    assert ds_map["smptsp"]["total_benchmark_instances"] == 10
    assert ds_map["smptsp"]["task_count_max"] == 1577


def test_full_vs_reduced_loading_integrity():
    from app.datasets.registry import dataset_registry

    # 1. Full SMPTSP loading
    full_sc, full_sum = dataset_registry.load_scenario("smptsp", "data_1_50_258_20_90_100_200_300", max_jobs=None)
    assert len(full_sc.shifts) == 258, "Full SMPTSP instance 1 must contain all 258 tasks"
    assert "Reduced Subset" not in full_sc.name

    # 2. Reduced SMPTSP loading
    red_sc, red_sum = dataset_registry.load_scenario("smptsp", "data_1_50_258_20_90_100_200_300", max_jobs=50)
    assert len(red_sc.shifts) == 50, "Reduced SMPTSP instance 1 must be capped at 50 tasks"
    assert "Reduced Subset" in red_sc.name
    assert "Reduced subset of 50/258 tasks" in red_sum.notes


def test_no_fabricated_timeout_results():
    bench_script = (BACKEND_DIR / "scripts" / "run_academic_benchmarks.py").read_text(encoding="utf-8")
    
    # Assert fabricated pattern is gone
    assert 'm_status = "TIME_LIMIT_EXCEEDED"\n            m_shifts = 0\n            m_assigned = 0\n            m_cov = 0.0\n            m_time = 30.0' not in bench_script
    
    # Assert MILP is genuinely solved using MILPTaskSolver across tiers
    assert "MILPTaskSolver(" in bench_script
    assert "m_res = MILPTaskSolver" in bench_script


def test_no_hardcoded_experimental_figures():
    art_script = (BACKEND_DIR / "scripts" / "generate_paper_artifacts.py").read_text(encoding="utf-8")
    
    # Assert fabricated cost/overtime/fairness lists are gone
    assert "cost_vals = [14200, 11850, 12600]" not in art_script
    assert "ot_vals = [48, 12, 18]" not in art_script
    assert "fairness_variance = [16.4, 12.8, 4.1]" not in art_script


def test_task_non_overlap_validator_detects_conflict():
    from app.optimization.task_allocation.task_models import Task, TaskWorker, TaskScenario, TaskAssignment
    from app.optimization.task_allocation.task_validator import validate_task_allocation

    tasks = [
        Task(id="t1", name="Task 1", start_minute=60, end_minute=120, duration_minutes=60),
        Task(id="t2", name="Task 2", start_minute=90, end_minute=150, duration_minutes=60), # Overlaps [90, 120)
    ]
    workers = [
        TaskWorker(id="w1", name="Worker 1", qualified_task_ids={"t1", "t2"}, max_hours=8.0)
    ]
    sc = TaskScenario(id="sc_test", name="Test", tasks=tasks, workers=workers)

    # Assign same worker to overlapping tasks
    assignments = [
        TaskAssignment(worker_id="w1", task_id="t1", start_minute=60, end_minute=120),
        TaskAssignment(worker_id="w1", task_id="t2", start_minute=90, end_minute=150),
    ]

    is_valid, violations = validate_task_allocation(sc, assignments)
    assert not is_valid, "Validator must reject overlapping interval assignments"
    assert any("overlapping" in v.lower() for v in violations)


def test_milp_resource_safety_threshold():
    from app.optimization.task_allocation.task_models import Task, TaskWorker, TaskScenario
    from app.optimization.task_allocation.task_milp_solver import MILPTaskSolver

    # Generate scenario with huge variable space
    tasks = [Task(id=f"t_{i}", name=f"Task {i}", start_minute=i*10, end_minute=i*10+60, duration_minutes=60) for i in range(100)]
    all_t = {t.id for t in tasks}
    workers = [TaskWorker(id=f"w_{w}", name=f"Worker {w}", qualified_task_ids=all_t, max_hours=8.0) for w in range(100)]
    sc = TaskScenario(id="sc_huge", name="Huge", tasks=tasks, workers=workers)

    # 100 workers * 100 tasks = 10,000 variables. Set threshold to 5,000
    solver = MILPTaskSolver(max_variables=5000)
    res = solver.solve(sc)

    assert res.status == "NOT_RUN_RESOURCE_LIMIT"
    assert "exceeds safe threshold" in res.message


def test_fair_disruption_recovery_results():
    rec_path = BENCH_DIR / "disruption_recovery_benchmarks.json"
    assert rec_path.exists(), "disruption_recovery_benchmarks.json must exist"

    with open(rec_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Verify both Recovery and Full Reschedule have valid status and non-empty coverage
    for r in data:
        assert r["status"] == "OPTIMAL", "Both recovery strategies must be OPTIMAL for fair comparison"
        assert r["coverage_repaired"] > 0, "Neither recovery strategy should have 0 coverage"
        assert r["is_valid"] is True, "Both rosters must be validated as strictly feasible"
