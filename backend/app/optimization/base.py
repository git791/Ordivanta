from abc import ABC, abstractmethod
from dataclasses import dataclass
from app.domain.models import Scenario, Assignment
from app.domain.enums import SolverStatus
from app.schemas.schedule import ObjectiveConfig


@dataclass
class SolveOutcome:
    status: SolverStatus
    assignments: list[Assignment]
    objective_value: float | None
    runtime_seconds: float
    message: str | None = None


class Scheduler(ABC):
    @abstractmethod
    def solve(
        self,
        scenario: Scenario,
        config: ObjectiveConfig,
        time_limit: int | None = None,
    ) -> SolveOutcome:
        ...


class SolverUnavailableError(Exception):
    pass
