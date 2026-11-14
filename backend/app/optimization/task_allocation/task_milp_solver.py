import time
import pulp
from typing import List, Dict, Set, Tuple
from .task_models import (
    TaskScenario,
    TaskAssignment,
    TaskAllocationResult,
    Task,
    TaskWorker,
)
from .task_validator import validate_task_allocation
from app.optimization.solver_adapter import get_solver, map_pulp_status


class MILPTaskSolver:
    """
    Exact Mixed-Integer Linear Programming (MILP) task-allocation solver for Module 2.
    Formulates interval-scheduling, multi-skilling qualifications, and shift minimisation
    using PuLP and the HiGHS/CBC solver adapter.
    """

    def __init__(self, time_limit: int = 30):
        self.time_limit = time_limit

    def solve(self, scenario: TaskScenario) -> TaskAllocationResult:
        start_time = time.perf_counter()

        tasks = scenario.tasks
        workers = scenario.workers
        task_map: Dict[str, Task] = {t.id: t for t in tasks}
        worker_map: Dict[str, TaskWorker] = {w.id: w for w in workers}

        prob = pulp.LpProblem(f"TaskAllocation_{scenario.id}", pulp.LpMinimize)

        def make_var(name: str, cat: str = "Binary", low_bound: float = 0.0, up_bound: float | None = 1.0):
            if hasattr(prob, "add_variable"):
                return prob.add_variable(name, lowBound=low_bound, upBound=up_bound, cat=cat)
            return pulp.LpVariable(name, lowBound=low_bound, upBound=up_bound, cat=cat)

        # 1. Variables
        # x[w, j]: binary, worker w assigned to task j
        x: Dict[Tuple[str, str], pulp.LpVariable] = {}
        for w in workers:
            for t_id in w.qualified_task_ids:
                if t_id in task_map:
                    x[(w.id, t_id)] = make_var(f"x_{w.id}_{t_id}", cat="Binary", low_bound=0.0, up_bound=1.0)

        # u[j]: binary, task j is unassigned
        u: Dict[str, pulp.LpVariable] = {
            t.id: make_var(f"u_{t.id}", cat="Binary", low_bound=0.0, up_bound=1.0) for t in tasks
        }

        # y[w]: binary, worker w is active (assigned at least 1 task / shift open)
        y: Dict[str, pulp.LpVariable] = {
            w.id: make_var(f"y_{w.id}", cat="Binary", low_bound=0.0, up_bound=1.0) for w in workers
        }

        # 2. Constraints

        # A. Coverage: sum_w x[w, j] + u[j] = 1 for all tasks
        for t in tasks:
            assigned_vars = [
                x[(w.id, t.id)]
                for w in workers
                if (w.id, t.id) in x
            ]
            if assigned_vars:
                prob += (
                    pulp.lpSum(assigned_vars) + u[t.id] == 1,
                    f"Coverage_{t.id}",
                )
            else:
                prob += u[t.id] == 1, f"NoQualifiedWorkers_{t.id}"

        # B. Worker activation linking: x[w, j] <= y[w]
        for (w_id, t_id), var in x.items():
            prob += var <= y[w_id], f"ActivateWorker_{w_id}_{t_id}"

        # C. Max daily working hours
        for w in workers:
            w_task_durations = [
                task_map[t_id].duration_minutes * x[(w.id, t_id)]
                for t_id in w.qualified_task_ids
                if (w.id, t_id) in x
            ]
            if w_task_durations:
                prob += (
                    pulp.lpSum(w_task_durations) <= w.max_hours * 60,
                    f"MaxHours_{w.id}",
                )

        # D. Temporal non-overlapping conflict constraints
        # Efficient sweep-line conflict detection
        sorted_tasks = sorted(tasks, key=lambda t: t.start_minute)
        overlap_pairs: List[Tuple[str, str]] = []
        n_tasks = len(sorted_tasks)
        for i in range(n_tasks):
            t1 = sorted_tasks[i]
            for j in range(i + 1, n_tasks):
                t2 = sorted_tasks[j]
                if t2.start_minute >= t1.end_minute:
                    break
                overlap_pairs.append((t1.id, t2.id))

        # Index qualified workers per task for fast intersection
        task_workers_map: Dict[str, Set[str]] = {t.id: set() for t in tasks}
        for w in workers:
            for t_id in w.qualified_task_ids:
                if t_id in task_workers_map:
                    task_workers_map[t_id].add(w.id)

        # Add conflict constraints only for workers qualified for BOTH overlapping tasks
        conflict_count = 0
        for t1_id, t2_id in overlap_pairs:
            common_workers = task_workers_map[t1_id] & task_workers_map[t2_id]
            for w_id in common_workers:
                prob += (
                    x[(w_id, t1_id)] + x[(w_id, t2_id)] <= 1,
                    f"Conf_{w_id}_{t1_id}_{t2_id}",
                )
                conflict_count += 1

        # 3. Objective Function
        if scenario.objective_type == "shift_minimization":
            # Primary: minimize active shifts/workers; Heavily penalize unassigned
            prob += (
                1000.0 * pulp.lpSum(y.values())
                + 50000.0 * pulp.lpSum(u.values())
                + 0.01 * pulp.lpSum(x.values()),
                "ShiftMinimizationObjective",
            )
        else:
            # Coverage balance objective
            prob += (
                20000.0 * pulp.lpSum(u.values())
                + 50.0 * pulp.lpSum(y.values())
                + 0.05 * pulp.lpSum(x.values()),
                "TaskCoverageObjective",
            )

        # 4. Solve with configured solver
        solver = get_solver(time_limit=self.time_limit)
        solve_res = prob.solve(solver)

        runtime = time.perf_counter() - start_time
        if hasattr(solve_res, "status"):
            raw_lp = solve_res.status
            raw_sol = 1 if getattr(solve_res, "has_solution", False) else None
        else:
            raw_lp = getattr(prob, "status", None)
            raw_sol = getattr(prob, "sol_status", None)

        solver_status, status_msg = map_pulp_status(raw_lp, raw_sol)

        # 5. Extract results
        assignments: List[TaskAssignment] = []
        unassigned_tasks: List[str] = []
        worker_minutes: Dict[str, int] = {w.id: 0 for w in workers}

        def get_val(v) -> float:
            if hasattr(v, "value") and callable(v.value):
                res = v.value()
                return float(res) if res is not None else 0.0
            if hasattr(v, "varValue") and v.varValue is not None:
                return float(v.varValue)
            try:
                res = pulp.value(v)
                return float(res) if res is not None else 0.0
            except Exception:
                return 0.0

        for (w_id, t_id), var in x.items():
            val = get_val(var)
            if val > 0.5:
                t = task_map[t_id]
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

        for t_id, var in u.items():
            val = get_val(var)
            if val > 0.5:
                unassigned_tasks.append(t_id)

        # Active workers count
        active_workers = {a.worker_id for a in assignments}
        active_shifts_count = len(active_workers)
        total_assigned = len(assignments)
        total_tasks = len(tasks)
        coverage_pct = (total_assigned / total_tasks * 100.0) if total_tasks > 0 else 100.0

        worker_utilization = {
            w_id: round(minutes / 60.0, 2)
            for w_id, minutes in worker_minutes.items()
            if minutes > 0
        }

        # Independent validation
        is_valid, violations = validate_task_allocation(scenario, assignments)

        obj_val = None
        try:
            val = pulp.value(prob.objective)
            if val is not None:
                obj_val = float(val)
        except Exception:
            pass

        status_str = solver_status.value if hasattr(solver_status, "value") else str(solver_status)

        return TaskAllocationResult(
            algorithm="Exact MILP Task Allocator",
            status=status_str,
            assignments=assignments,
            unassigned_tasks=unassigned_tasks,
            active_workers_count=active_shifts_count,
            total_assigned=total_assigned,
            total_tasks=total_tasks,
            coverage_percentage=coverage_pct,
            runtime_seconds=runtime,
            objective_value=obj_val,
            worker_utilization_hours=worker_utilization,
            is_valid=is_valid,
            validation_violations=violations,
            message=status_msg or f"MILP solved {total_assigned}/{total_tasks} tasks with {active_shifts_count} shifts in {runtime:.4f}s",
        )
