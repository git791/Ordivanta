import time
from typing import List, Dict, Set
from .task_models import (
    TaskScenario,
    TaskAssignment,
    TaskAllocationResult,
    Task,
    TaskWorker,
)
from .task_validator import validate_task_allocation


class GreedyTaskSolver:
    """
    Greedy Interval-Scheduling heuristic with shift-minimization heuristics for Module 2.
    Sorts tasks by earliest start time and packs them into active qualified workers
    to minimize the number of distinct workers (shifts) activated.
    """

    def solve(self, scenario: TaskScenario) -> TaskAllocationResult:
        start_time = time.perf_counter()

        # Sort tasks by start minute, then duration
        sorted_tasks = sorted(
            scenario.tasks,
            key=lambda t: (t.start_minute, t.duration_minutes),
        )

        task_map: Dict[str, Task] = {t.id: t for t in scenario.tasks}
        worker_map: Dict[str, TaskWorker] = {w.id: w for w in scenario.workers}

        # Track assignments per worker
        worker_assigned_tasks: Dict[str, List[Task]] = {w.id: [] for w in scenario.workers}
        worker_assigned_minutes: Dict[str, int] = {w.id: 0 for w in scenario.workers}

        assignments: List[TaskAssignment] = []
        unassigned: List[str] = []

        for task in sorted_tasks:
            best_worker_id = None
            best_score = float("inf")

            # Find eligible workers
            for worker in scenario.workers:
                # 1. Qualification check
                if task.id not in worker.qualified_task_ids:
                    continue

                # 2. Daily hours check
                if worker_assigned_minutes[worker.id] + task.duration_minutes > worker.max_hours * 60:
                    continue

                # 3. Temporal overlap check with already assigned tasks for this worker
                has_conflict = False
                for assigned_t in worker_assigned_tasks[worker.id]:
                    if task.overlaps_with(assigned_t):
                        has_conflict = True
                        break
                if has_conflict:
                    continue

                # Scoring: Strongly prefer already-active workers (SMPTSP objective)
                is_active = len(worker_assigned_tasks[worker.id]) > 0
                if is_active:
                    # Find min idle time gap
                    last_end = max(t.end_minute for t in worker_assigned_tasks[worker.id])
                    gap = abs(task.start_minute - last_end)
                    # Active worker score is gap (smaller gap = tighter pack)
                    score = gap
                else:
                    # Inactive worker activation penalty
                    score = 100000.0 + len(worker.qualified_task_ids)

                if score < best_score:
                    best_score = score
                    best_worker_id = worker.id

            if best_worker_id:
                worker_assigned_tasks[best_worker_id].append(task)
                worker_assigned_minutes[best_worker_id] += task.duration_minutes
                assignments.append(
                    TaskAssignment(
                        worker_id=best_worker_id,
                        task_id=task.id,
                        start_minute=task.start_minute,
                        end_minute=task.end_minute,
                        worker_name=worker_map[best_worker_id].name,
                        task_name=task.name,
                    )
                )
            else:
                unassigned.append(task.id)

        runtime = time.perf_counter() - start_time

        # Calculate metrics
        active_workers = {a.worker_id for a in assignments}
        active_shifts_count = len(active_workers)
        total_assigned = len(assignments)
        total_tasks = len(scenario.tasks)
        coverage_pct = (total_assigned / total_tasks * 100.0) if total_tasks > 0 else 100.0

        worker_utilization = {
            w_id: round(minutes / 60.0, 2)
            for w_id, minutes in worker_assigned_minutes.items()
            if minutes > 0
        }

        # Independent validation
        is_valid, violations = validate_task_allocation(scenario, assignments)

        # Objective calculation: shifts + unassigned penalty
        objective_value = (
            active_shifts_count * 100.0
            + len(unassigned) * 1000.0
            + sum(worker_utilization.values()) * 0.1
        )

        status = "FEASIBLE" if is_valid and len(unassigned) == 0 else ("PARTIAL" if is_valid else "ERROR")

        return TaskAllocationResult(
            algorithm="Greedy Task Allocator",
            status=status,
            assignments=assignments,
            unassigned_tasks=unassigned,
            active_workers_count=active_shifts_count,
            total_assigned=total_assigned,
            total_tasks=total_tasks,
            coverage_percentage=coverage_pct,
            runtime_seconds=runtime,
            objective_value=objective_value,
            worker_utilization_hours=worker_utilization,
            is_valid=is_valid,
            validation_violations=violations,
            message=f"Greedy allocated {total_assigned}/{total_tasks} tasks across {active_shifts_count} workers in {runtime:.4f}s",
        )
