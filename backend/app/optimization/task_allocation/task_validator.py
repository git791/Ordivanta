from typing import List, Tuple
from .task_models import TaskScenario, TaskAssignment, Task


def validate_task_allocation(
    scenario: TaskScenario,
    assignments: List[TaskAssignment],
) -> Tuple[bool, List[str]]:
    """
    Independently validate task allocation against original constraints:
    1. Qualifications: Worker must be qualified for assigned task.
    2. Temporal conflicts: Worker cannot execute overlapping tasks simultaneously.
    3. Single assignment: A task cannot be assigned to more than 1 worker.
    4. Working hours: Worker total duration cannot exceed max_hours.
    """
    violations: List[str] = []
    task_map: dict[str, Task] = {t.id: t for t in scenario.tasks}
    worker_map = {w.id: w for w in scenario.workers}

    # 1. Single assignment check
    seen_tasks = set()
    for a in assignments:
        if a.task_id in seen_tasks:
            violations.append(f"Task '{a.task_id}' assigned multiple times.")
        seen_tasks.add(a.task_id)

    # 2. Group assignments by worker
    worker_assignments: dict[str, List[TaskAssignment]] = {}
    for a in assignments:
        worker_assignments.setdefault(a.worker_id, []).append(a)

    for worker_id, w_assigns in worker_assignments.items():
        worker = worker_map.get(worker_id)
        if not worker:
            violations.append(f"Unknown worker '{worker_id}' in assignments.")
            continue

        # Check qualifications
        for a in w_assigns:
            if a.task_id not in worker.qualified_task_ids:
                violations.append(
                    f"Worker '{worker_id}' is NOT qualified for task '{a.task_id}'."
                )

        # Check total hours
        total_duration_minutes = sum(
            task_map[a.task_id].duration_minutes
            for a in w_assigns
            if a.task_id in task_map
        )
        if total_duration_minutes > worker.max_hours * 60 + 1e-4:
            violations.append(
                f"Worker '{worker_id}' scheduled for {total_duration_minutes/60:.2f}h, exceeding max {worker.max_hours:.2f}h."
            )

        # Check pairwise temporal conflicts
        sorted_assigns = sorted(
            w_assigns, key=lambda a: (task_map[a.task_id].start_minute if a.task_id in task_map else a.start_minute)
        )
        for i in range(len(sorted_assigns)):
            for j in range(i + 1, len(sorted_assigns)):
                a1 = sorted_assigns[i]
                a2 = sorted_assigns[j]
                t1 = task_map.get(a1.task_id)
                t2 = task_map.get(a2.task_id)
                if t1 and t2:
                    if t1.overlaps_with(t2):
                        violations.append(
                            f"Worker '{worker_id}' has overlapping tasks: "
                            f"'{t1.id}' [{t1.start_time_str}-{t1.end_time_str}] and "
                            f"'{t2.id}' [{t2.start_time_str}-{t2.end_time_str}]."
                        )

    return len(violations) == 0, violations
