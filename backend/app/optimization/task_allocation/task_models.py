from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from app.domain.models import Scenario


@dataclass
class Task:
    id: str
    name: str
    start_minute: int
    end_minute: int
    duration_minutes: int
    required_skill: str = "task_skill"
    workstation: str = "cell_1"

    @property
    def start_time_str(self) -> str:
        return f"{self.start_minute // 60:02d}:{self.start_minute % 60:02d}"

    @property
    def end_time_str(self) -> str:
        return f"{self.end_minute // 60:02d}:{self.end_minute % 60:02d}"

    def overlaps_with(self, other: "Task") -> bool:
        """Return True if two tasks overlap in time (strictly interior intersection)."""
        return max(self.start_minute, other.start_minute) < min(self.end_minute, other.end_minute)


@dataclass
class TaskWorker:
    id: str
    name: str
    qualified_task_ids: Set[str] = field(default_factory=set)
    skills: List[str] = field(default_factory=lambda: ["task_skill"])
    max_hours: float = 24.0


@dataclass
class TaskScenario:
    id: str
    name: str
    tasks: List[Task]
    workers: List[TaskWorker]
    objective_type: str = "shift_minimization"  # "shift_minimization" (SMPTSP) or "coverage_balance" (PTSP)
    source_dataset: str = "smptsp"

    @classmethod
    def from_domain_scenario(cls, scenario: Scenario, objective_type: str = "shift_minimization") -> "TaskScenario":
        """Convert a standard Scenario loaded from PTSP or SMPTSP loader into a TaskScenario."""
        tasks: List[Task] = []
        for s in scenario.shifts:
            # Shift id is e.g. "job_0"
            # Try to parse start_time and end_time
            start_m = 0
            end_m = int(s.duration_hours * 60)
            if s.start_time and ":" in s.start_time:
                parts = s.start_time.split(":")
                start_m = int(parts[0]) * 60 + int(parts[1])
            if s.end_time and ":" in s.end_time:
                parts = s.end_time.split(":")
                end_m = int(parts[0]) * 60 + int(parts[1])
                if end_m <= start_m:
                    end_m = start_m + max(15, int(s.duration_hours * 60))
            else:
                end_m = start_m + max(15, int(s.duration_hours * 60))

            tasks.append(
                Task(
                    id=s.id,
                    name=s.name or s.id,
                    start_minute=start_m,
                    end_minute=end_m,
                    duration_minutes=max(15, end_m - start_m),
                    required_skill="task_skill",
                )
            )

        workers: List[TaskWorker] = []
        for e in scenario.employees:
            q_tasks = set(e.available_shifts) if e.available_shifts else {t.id for t in tasks}
            workers.append(
                TaskWorker(
                    id=e.id,
                    name=e.name or e.id,
                    qualified_task_ids=q_tasks,
                    skills=e.skills,
                    max_hours=e.max_hours,
                )
            )

        return cls(
            id=scenario.id,
            name=scenario.name,
            tasks=tasks,
            workers=workers,
            objective_type=objective_type,
            source_dataset="ptsp" if "ptsp" in scenario.id.lower() else "smptsp",
        )


@dataclass
class TaskAssignment:
    worker_id: str
    task_id: str
    start_minute: int
    end_minute: int
    worker_name: str = ""
    task_name: str = ""


@dataclass
class TaskAllocationResult:
    algorithm: str
    status: str  # "OPTIMAL", "FEASIBLE", "INFEASIBLE", "NOT_SOLVED"
    assignments: List[TaskAssignment]
    unassigned_tasks: List[str]
    active_workers_count: int
    total_assigned: int
    total_tasks: int
    coverage_percentage: float
    runtime_seconds: float
    objective_value: Optional[float] = None
    worker_utilization_hours: Dict[str, float] = field(default_factory=dict)
    is_valid: bool = True
    validation_violations: List[str] = field(default_factory=list)
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "status": self.status,
            "assignments": [
                {
                    "worker_id": a.worker_id,
                    "task_id": a.task_id,
                    "start_minute": a.start_minute,
                    "end_minute": a.end_minute,
                    "worker_name": a.worker_name,
                    "task_name": a.task_name,
                }
                for a in self.assignments
            ],
            "unassigned_tasks": self.unassigned_tasks,
            "active_workers_count": self.active_workers_count,
            "total_assigned": self.total_assigned,
            "total_tasks": self.total_tasks,
            "coverage_percentage": round(self.coverage_percentage, 2),
            "runtime_seconds": round(self.runtime_seconds, 4),
            "objective_value": round(self.objective_value, 4) if self.objective_value is not None else None,
            "worker_utilization_hours": {
                k: round(v, 2) for k, v in self.worker_utilization_hours.items()
            },
            "is_valid": self.is_valid,
            "validation_violations": self.validation_violations,
            "message": self.message,
        }
