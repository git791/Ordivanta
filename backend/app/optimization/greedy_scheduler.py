import time
from app.domain.models import Scenario, Assignment
from app.domain.enums import SolverStatus
from app.schemas.schedule import ObjectiveConfig
from .base import Scheduler, SolveOutcome


class GreedyScheduler(Scheduler):
    """
    Deterministic greedy baseline scheduler.
    Sorts demands by required headcount descending and assigns candidate employees
    with the most remaining capacity.
    Greedy never claims optimality and always returns FEASIBLE or INFEASIBLE.
    """

    def solve(
        self,
        scenario: Scenario,
        config: ObjectiveConfig,
        time_limit: int | None = None,
    ) -> SolveOutcome:
        start_time = time.perf_counter()

        unit_map = {u.id: u for u in scenario.units}
        shift_durations = {s.id: s.duration_hours for s in scenario.shifts}

        assigned_shifts: dict[str, set[str]] = {e.id: set() for e in scenario.employees}
        assigned_hours: dict[str, float] = {e.id: 0.0 for e in scenario.employees}

        assignments: list[Assignment] = []
        shortages = 0

        # Sort demands by required_headcount descending, then deterministic tie-breaker
        sorted_demands = sorted(
            scenario.demands,
            key=lambda d: (-d.required_headcount, d.unit_id, d.shift_id),
        )

        for d in sorted_demands:
            shift_duration = shift_durations.get(d.shift_id, 0.0)
            target_unit = unit_map.get(d.unit_id)
            req_skills = target_unit.required_skills if target_unit else []

            # Identify eligible candidates
            candidates = []
            for emp in scenario.employees:
                # 1. Availability check
                if d.shift_id not in emp.available_shifts:
                    continue
                # 2. Qualification check
                if req_skills and not any(sk in req_skills for sk in emp.skills):
                    continue
                # 3. One assignment per shift check
                if d.shift_id in assigned_shifts[emp.id]:
                    continue
                # 4. Max scheduled hours check
                if assigned_hours[emp.id] + shift_duration > emp.max_hours:
                    continue

                candidates.append(emp)

            # Sort candidates by remaining hours descending (most capacity first), then ID for determinism
            candidates.sort(
                key=lambda e: (-(e.max_hours - assigned_hours[e.id]), e.id)
            )

            # Assign up to required_headcount
            allocated = 0
            for cand in candidates:
                if allocated >= d.required_headcount:
                    break
                assignments.append(
                    Assignment(
                        employee_id=cand.id,
                        unit_id=d.unit_id,
                        shift_id=d.shift_id,
                        hours=shift_duration,
                    )
                )
                assigned_shifts[cand.id].add(d.shift_id)
                assigned_hours[cand.id] += shift_duration
                allocated += 1

            if allocated < d.required_headcount:
                shortages += (d.required_headcount - allocated)

        runtime_seconds = time.perf_counter() - start_time

        # Status determination: Greedy never proves optimality
        if shortages > 0:
            status = SolverStatus.INFEASIBLE
            message = f"Greedy heuristic could not satisfy all demand ({shortages} positions unfilled)"
        else:
            status = SolverStatus.FEASIBLE
            message = "Feasible schedule found (Greedy heuristic does not prove optimality)"

        return SolveOutcome(
            status=status,
            assignments=assignments,
            objective_value=None,
            runtime_seconds=runtime_seconds,
            message=message,
        )
