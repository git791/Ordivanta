import time
import math
import random
from typing import List, Dict, Set, Tuple
from .task_models import (
    TaskScenario,
    TaskAssignment,
    TaskAllocationResult,
    Task,
    TaskWorker,
)
from .task_validator import validate_task_allocation
from .task_greedy_solver import GreedyTaskSolver


class ALNSTaskSolver:
    """
    Adaptive Large Neighborhood Search (ALNS) Metaheuristic for Module 2.
    Utilizes destroy operators (Random, Temporal Window, Shift Consolidation)
    and repair operators (Regret-2, Shift-Minimizing Best-Fit) with Simulated Annealing
    acceptance to find high-quality solutions for large-scale instances rapidly.
    """

    def __init__(self, max_iterations: int = 150, time_limit: float = 20.0, seed: int = 42):
        self.max_iterations = max_iterations
        self.time_limit = time_limit
        self.seed = seed

    def solve(self, scenario: TaskScenario) -> TaskAllocationResult:
        start_time = time.perf_counter()
        rng = random.Random(self.seed)

        task_map: Dict[str, Task] = {t.id: t for t in scenario.tasks}
        worker_map: Dict[str, TaskWorker] = {w.id: w for w in scenario.workers}

        # 1. Generate initial solution using Greedy baseline
        greedy = GreedyTaskSolver()
        initial_result = greedy.solve(scenario)

        # Represent solution as mapping: task_id -> worker_id (or None if unassigned)
        current_sol: Dict[str, str | None] = {t.id: None for t in scenario.tasks}
        for a in initial_result.assignments:
            current_sol[a.task_id] = a.worker_id

        def eval_solution(sol: Dict[str, str | None]) -> float:
            """Evaluate objective cost: 1000 per active shift + 50000 per unassigned task."""
            active_w = {w_id for w_id in sol.values() if w_id is not None}
            unassigned_cnt = sum(1 for w_id in sol.values() if w_id is None)
            return len(active_w) * 1000.0 + unassigned_cnt * 50000.0

        current_cost = eval_solution(current_sol)
        best_sol = dict(current_sol)
        best_cost = current_cost

        # Simulated Annealing temperature
        T = max(100.0, current_cost * 0.1)
        cooling_rate = 0.95

        destroy_weights = [1.0, 1.0, 1.0]  # Random, Window, Low-Worker
        repair_weights = [1.0, 1.0]        # Regret-2, Greedy-BestFit

        # Pre-build qualified workers mapping for each task
        task_qualified_workers: Dict[str, List[str]] = {t.id: [] for t in scenario.tasks}
        for w in scenario.workers:
            for t_id in w.qualified_task_ids:
                if t_id in task_qualified_workers:
                    task_qualified_workers[t_id].append(w.id)

        # Helper to check if task can be assigned to worker without conflicts
        def can_assign_to(w_id: str, t: Task, w_tasks: List[Task]) -> bool:
            w = worker_map[w_id]
            for other_t in w_tasks:
                if t.overlaps_with(other_t):
                    return False
            total_min = sum(ot.duration_minutes for ot in w_tasks) + t.duration_minutes
            if total_min > w.max_hours * 60:
                return False
            return True

        # Search loop
        for iteration in range(self.max_iterations):
            if time.perf_counter() - start_time >= self.time_limit:
                break

            working_sol = dict(current_sol)

            # Build worker -> list of assigned tasks lookup
            worker_tasks: Dict[str, List[Task]] = {w_id: [] for w_id in worker_map}
            for t_id, w_id in working_sol.items():
                if w_id is not None:
                    worker_tasks[w_id].append(task_map[t_id])

            # Choose destroy operator
            total_d_w = sum(destroy_weights)
            r_d = rng.uniform(0, total_d_w)
            d_op = 0 if r_d <= destroy_weights[0] else (1 if r_d <= destroy_weights[0] + destroy_weights[1] else 2)

            unassigned_pool: List[str] = [t_id for t_id, w_id in working_sol.items() if w_id is None]

            if d_op == 0:
                # Random removal: remove 15-20% of assigned tasks
                assigned_keys = [t_id for t_id, w_id in working_sol.items() if w_id is not None]
                k = min(len(assigned_keys), max(2, int(len(assigned_keys) * 0.15)))
                to_remove = rng.sample(assigned_keys, k)
                for t_id in to_remove:
                    old_w = working_sol[t_id]
                    working_sol[t_id] = None
                    if old_w and task_map[t_id] in worker_tasks[old_w]:
                        worker_tasks[old_w].remove(task_map[t_id])
                    unassigned_pool.append(t_id)

            elif d_op == 1:
                # Temporal Window removal: unassign tasks in a random 120-minute window
                win_start = rng.randint(0, 1300)
                win_end = win_start + 120
                for t_id, w_id in list(working_sol.items()):
                    if w_id is not None:
                        t = task_map[t_id]
                        if t.start_minute < win_end and t.end_minute > win_start:
                            working_sol[t_id] = None
                            if task_map[t_id] in worker_tasks[w_id]:
                                worker_tasks[w_id].remove(task_map[t_id])
                            unassigned_pool.append(t_id)

            else:
                # Shift Consolidation: remove tasks from least-utilized worker
                active_workers = [w_id for w_id, t_list in worker_tasks.items() if t_list]
                if active_workers:
                    worker_loads = {
                        w_id: sum(t.duration_minutes for t in worker_tasks[w_id])
                        for w_id in active_workers
                    }
                    min_worker = min(worker_loads, key=worker_loads.get)
                    for t in list(worker_tasks[min_worker]):
                        working_sol[t.id] = None
                        unassigned_pool.append(t.id)
                    worker_tasks[min_worker].clear()

            # Choose repair operator
            total_r_w = sum(repair_weights)
            r_r = rng.uniform(0, total_r_w)
            r_op = 0 if r_r <= repair_weights[0] else 1

            # Repair: reassign unassigned tasks
            rng.shuffle(unassigned_pool)

            if r_op == 0:
                # Regret-2 insertion with candidate sampling
                while unassigned_pool:
                    if time.perf_counter() - start_time >= self.time_limit:
                        break
                    best_task_idx = 0
                    best_w = None
                    max_regret = -1.0

                    # Sample up to 15 candidates for fast regret evaluation
                    eval_sample = unassigned_pool[:15]

                    for idx, t_id in enumerate(eval_sample):
                        t = task_map[t_id]
                        eligible = task_qualified_workers.get(t_id, [])
                        feasible_costs = []

                        for w_id in eligible:
                            if can_assign_to(w_id, t, worker_tasks[w_id]):
                                is_act = len(worker_tasks[w_id]) > 0
                                cost = 0.0 if is_act else 1000.0
                                feasible_costs.append((cost, w_id))

                        if not feasible_costs:
                            continue

                        feasible_costs.sort(key=lambda x: x[0])
                        first_cost, first_w = feasible_costs[0]
                        second_cost = feasible_costs[1][0] if len(feasible_costs) > 1 else 2000.0
                        regret = second_cost - first_cost

                        if regret > max_regret:
                            max_regret = regret
                            best_task_idx = idx
                            best_w = first_w

                    if best_w is not None:
                        t_to_assign = unassigned_pool.pop(best_task_idx)
                        working_sol[t_to_assign] = best_w
                        worker_tasks[best_w].append(task_map[t_to_assign])
                    else:
                        break

            else:
                # Shift-Minimizing Best-Fit Insertion
                for t_id in list(unassigned_pool):
                    if time.perf_counter() - start_time >= self.time_limit:
                        break
                    t = task_map[t_id]
                    eligible = task_qualified_workers.get(t_id, [])
                    # Try active workers first
                    assigned = False
                    for w_id in eligible:
                        if worker_tasks[w_id] and can_assign_to(w_id, t, worker_tasks[w_id]):
                            working_sol[t_id] = w_id
                            worker_tasks[w_id].append(t)
                            unassigned_pool.remove(t_id)
                            assigned = True
                            break
                    if not assigned:
                        # Try activating idle worker
                        for w_id in eligible:
                            if not worker_tasks[w_id] and can_assign_to(w_id, t, worker_tasks[w_id]):
                                working_sol[t_id] = w_id
                                worker_tasks[w_id].append(t)
                                unassigned_pool.remove(t_id)
                                break

            # Acceptance check
            cand_cost = eval_solution(working_sol)
            delta = cand_cost - current_cost

            if delta < 0 or rng.random() < math.exp(-delta / max(1.0, T)):
                current_sol = dict(working_sol)
                current_cost = cand_cost
                if cand_cost < best_cost:
                    best_sol = dict(working_sol)
                    best_cost = cand_cost
                    # Reward operators
                    destroy_weights[d_op] += 0.2
                    repair_weights[r_op] += 0.2

            T *= cooling_rate

        runtime = time.perf_counter() - start_time

        # Build final assignments from best_sol
        assignments: List[TaskAssignment] = []
        unassigned_tasks: List[str] = []
        worker_minutes: Dict[str, int] = {w.id: 0 for w in scenario.workers}

        for t_id, w_id in best_sol.items():
            t = task_map[t_id]
            if w_id is not None:
                assignments.append(
                    TaskAssignment(
                        worker_id=w_id,
                        task_id=t_id,
                        start_minute=t.start_minute,
                        end_minute=t.end_minute,
                        worker_name=worker_map[w_id].name,
                        task_name=t.name,
                    )
                )
                worker_minutes[w_id] += t.duration_minutes
            else:
                unassigned_tasks.append(t_id)

        active_workers = {a.worker_id for a in assignments}
        active_shifts_count = len(active_workers)
        total_assigned = len(assignments)
        total_tasks = len(scenario.tasks)
        coverage_pct = (total_assigned / total_tasks * 100.0) if total_tasks > 0 else 100.0

        worker_utilization = {
            w_id: round(minutes / 60.0, 2)
            for w_id, minutes in worker_minutes.items()
            if minutes > 0
        }

        is_valid, violations = validate_task_allocation(scenario, assignments)
        status = "FEASIBLE" if is_valid and len(unassigned_tasks) == 0 else ("PARTIAL" if is_valid else "ERROR")

        return TaskAllocationResult(
            algorithm="ALNS Task Metaheuristic",
            status=status,
            assignments=assignments,
            unassigned_tasks=unassigned_tasks,
            active_workers_count=active_shifts_count,
            total_assigned=total_assigned,
            total_tasks=total_tasks,
            coverage_percentage=coverage_pct,
            runtime_seconds=runtime,
            objective_value=best_cost,
            worker_utilization_hours=worker_utilization,
            is_valid=is_valid,
            validation_violations=violations,
            message=f"ALNS allocated {total_assigned}/{total_tasks} tasks across {active_shifts_count} shifts in {runtime:.4f}s",
        )
