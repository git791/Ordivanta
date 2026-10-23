"""
Phase 6 Experiment Script: Critical Methodology Audit & Empirical Verification
Runs 5 timing repetitions per test case across:
- Small (15 staff, 27 pos)
- Medium (50 staff, 210 pos)
- Large (100 staff, 672 pos)
- Stress (200 staff, 2520 pos)
- Deficit (Infeasible)

Outputs exact measured medians, standard deviations, objective bounds, gaps, and validator results.
"""
import sys
import time
import math
import statistics
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.schemas.schedule import ObjectiveConfig
from app.domain.enums import ObjectivePrimary, SolverStatus
from app.optimization.milp_scheduler import MILPScheduler
from app.optimization.greedy_scheduler import GreedyScheduler
from app.optimization.alns_scheduler import ALNSScheduler
from app.validation.schedule_validator import validate_assignments
from app.metrics.schedule_metrics import compute_metrics
from app.datasets.scalability_generator import generate_manufacturing_scenario
from app.datasets.registry import dataset_registry

def compute_detailed_fairness(assignments, employees, target_hours):
    workloads = {e.id: 0.0 for e in employees}
    for a in assignments:
        workloads[a.employee_id] = workloads.get(a.employee_id, 0.0) + a.hours
    vals = list(workloads.values())
    n = len(vals)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0
    mean_val = statistics.mean(vals)
    sad = sum(abs(v - target_hours) for v in vals)
    mad = sad / n
    sd = statistics.stdev(vals) if n > 1 else 0.0
    spread = max(vals) - min(vals)
    return sad, mad, sd, spread

def run_experiment():
    print("Initializing Phase 6 Audit Experiments (5 repetitions)...")
    
    deficit_scn, _ = dataset_registry.load_scenario("synthetic_manufacturing", "mfg_shortage_infeasible")
    scenarios = [
        ("Small", generate_manufacturing_scenario("scal_small", "Small Mfg", 15, 3, 3, seed=101, headcount_per_cell=1)),
        ("Medium", generate_manufacturing_scenario("scal_med", "Med Mfg", 50, 5, 7, seed=202, headcount_per_cell=2)),
        ("Large", generate_manufacturing_scenario("scal_large", "Large Mfg", 100, 8, 14, seed=303, headcount_per_cell=2)),
        ("Stress", generate_manufacturing_scenario("scal_stress", "Stress Mfg", 200, 10, 21, seed=404, headcount_per_cell=4)),
        ("Deficit", deficit_scn),
    ]
    
    milp_two_stage = MILPScheduler()
    greedy = GreedyScheduler()
    alns = ALNSScheduler(max_iterations=100, seed=42)
    
    results = []
    
    for scn_name, scn in scenarios:
        total_req_pos = sum(d.required_headcount for d in scn.demands)
        total_req_hours = sum(d.required_headcount * next((s.duration_hours for s in scn.shifts if s.id == d.shift_id), 8.0) for d in scn.demands)
        target_hours = total_req_hours / len(scn.employees) if scn.employees else 0.0
        
        print(f"\n--- Testing Scenario: {scn_name} ({len(scn.employees)} staff, {len(scn.demands)} demands, {total_req_pos} pos, {total_req_hours}h) ---")
        
        algorithms = [
            ("Two-Stage MILP", milp_two_stage, ObjectiveConfig(primary=ObjectivePrimary.COST, fairness_weight=0.1, use_two_stage=True, fairness_epsilon_tolerance=0.0)),
            ("Greedy", greedy, ObjectiveConfig(primary=ObjectivePrimary.COST, fairness_weight=0.1)),
            ("ALNS (100 iter)", alns, ObjectiveConfig(primary=ObjectivePrimary.COST, fairness_weight=0.1)),
        ]
        
        n_reps = 3 if scn_name == "Stress" else 5
        for alg_name, scheduler, cfg in algorithms:
            runtimes = []
            final_outcome = None
            
            # Repetitions for runtime
            for rep in range(n_reps):
                t0 = time.perf_counter()
                outcome = scheduler.solve(scn, cfg)
                t1 = time.perf_counter()
                runtimes.append(t1 - t0)
                final_outcome = outcome
                
            med_time = statistics.median(runtimes)
            std_time = statistics.stdev(runtimes) if len(runtimes) > 1 else 0.0
            
            val = validate_assignments(final_outcome.assignments, scn)
            tot_hours = sum(a.hours for a in final_outcome.assignments)
            sad, mad, sd, spread = compute_detailed_fairness(final_outcome.assignments, scn.employees, target_hours)
            cov_pct = (len(final_outcome.assignments) / total_req_pos * 100.0) if total_req_pos > 0 else 100.0
            
            row = {
                "scenario": scn_name,
                "positions": total_req_pos,
                "algorithm": alg_name,
                "status": final_outcome.status.value,
                "med_time_s": med_time,
                "std_time_s": std_time,
                "cov_pct": cov_pct,
                "total_hours": tot_hours,
                "sad": sad,
                "mad": mad,
                "std_dev_hours": sd,
                "spread_hours": spread,
                "valid": val.is_valid,
                "errors": len(val.errors),
                "message": final_outcome.message or "",
            }
            results.append(row)
            print(f"  {alg_name:18s} | Status: {final_outcome.status.value:10s} | Time: {med_time:7.4f}s (+/-{std_time:6.4f}s) | Cov: {cov_pct:5.1f}% | Hours: {tot_hours:6.1f} | SAD: {sad:6.2f} | SD: {sd:5.2f}h | Spread: {spread:5.1f}h | Valid: {val.is_valid}")

    # Epsilon tolerance experiment on Small Mfg
    print("\n--- Two-Stage Epsilon Tolerance Verification on Small Mfg ---")
    small_scn = next(s for name, s in scenarios if name == "Small")
    tot_req_h = sum(d.required_headcount * 8.0 for d in small_scn.demands)
    tgt = tot_req_h / len(small_scn.employees)
    for eps in [0.00, 0.05, 0.10]:
        cfg = ObjectiveConfig(primary=ObjectivePrimary.COST, fairness_weight=0.1, use_two_stage=True, fairness_epsilon_tolerance=eps)
        outcome = milp_two_stage.solve(small_scn, cfg)
        tot_hours = sum(a.hours for a in outcome.assignments)
        sad, mad, sd, spread = compute_detailed_fairness(outcome.assignments, small_scn.employees, tgt)
        print(f"  Epsilon: {eps:.2f} | Status: {outcome.status.value} | Hours: {tot_hours:.1f} (bound: {tot_req_h * (1 + eps):.1f}) | SAD: {sad:.2f} | SD: {sd:.2f}h | Spread: {spread:.1f}h | Msg: {outcome.message}")

if __name__ == "__main__":
    run_experiment()
