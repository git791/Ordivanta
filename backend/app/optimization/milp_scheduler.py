import time
import pulp
from app.domain.models import Scenario, Assignment
from app.domain.enums import SolverStatus, ObjectivePrimary
from app.schemas.schedule import ObjectiveConfig
from .base import Scheduler, SolveOutcome, SolverUnavailableError
from .solver_adapter import get_solver, map_pulp_status


class MILPScheduler(Scheduler):
    """
    Mixed-Integer Linear Programming scheduler using PuLP and configured solver adapter.
    Enforces coverage, availability, qualifications, single assignment per shift, and max hours.
    """

    def solve(
        self,
        scenario: Scenario,
        config: ObjectiveConfig,
        time_limit: int | None = None,
    ) -> SolveOutcome:
        start_time = time.perf_counter()

        try:
            # 1. Build indices and lookups
            emp_ids = [e.id for e in scenario.employees]
            unit_ids = [u.id for u in scenario.units]
            shift_ids = [s.id for s in scenario.shifts]

            shift_durations = {s.id: s.duration_hours for s in scenario.shifts}
            emp_max_hours = {e.id: e.max_hours for e in scenario.employees}

            availability = {
                e.id: {s_id: (s_id in e.available_shifts) for s_id in shift_ids}
                for e in scenario.employees
            }

            qualified = {
                e.id: {
                    u.id: (len(u.required_skills) == 0 or any(sk in u.required_skills for sk in e.skills))
                    for u in scenario.units
                }
                for e in scenario.employees
            }

            # 2. Initialize PuLP model
            model = pulp.LpProblem("ordivanta_schedule", pulp.LpMinimize)

            # 3. Create binary decision variables
            # Only instantiate LpVariable when employee is available and qualified; otherwise set 0
            x: dict[tuple[str, str, str], pulp.LpVariable | int] = {}
            for i in emp_ids:
                for j in unit_ids:
                    for s in shift_ids:
                        if availability[i][s] and qualified[i][j]:
                            var_name = f"x_{i}_{j}_{s}"
                            if hasattr(model, "add_variable"):
                                x[(i, j, s)] = model.add_variable(var_name, cat="Binary")
                            else:
                                x[(i, j, s)] = pulp.LpVariable(var_name, cat="Binary")
                        else:
                            x[(i, j, s)] = 0

            # 4. Hard Constraints

            # Coverage: sum_i x_{ijs} >= demand_{js} for all configured demands
            for d in scenario.demands:
                model += (
                    pulp.lpSum(x.get((i, d.unit_id, d.shift_id), 0) for i in emp_ids) >= d.required_headcount,
                    f"coverage_{d.unit_id}_{d.shift_id}",
                )

            # One unit assignment per employee per shift: sum_j x_{ijs} <= 1 for each (i, s)
            for i in emp_ids:
                for s in shift_ids:
                    model += (
                        pulp.lpSum(x.get((i, j, s), 0) for j in unit_ids) <= 1,
                        f"one_shift_{i}_{s}",
                    )

            # Max scheduled hours: sum_{j,s} duration_s * x_{ijs} <= max_hours_i for each i
            for i in emp_ids:
                model += (
                    pulp.lpSum(
                        shift_durations.get(s, 0.0) * x.get((i, j, s), 0)
                        for j in unit_ids
                        for s in shift_ids
                    )
                    <= emp_max_hours[i],
                    f"max_hours_{i}",
                )

            # 5. Objective formulation
            # Default is feasibility (objective = 0)
            if config.primary == ObjectivePrimary.COST:
                # If cost data exists on assignments in future iterations, plug it here; default to 0
                model += 0
            else:
                model += 0

            # 6. Solve model with configured adapter
            solver = get_solver(time_limit=time_limit)
            solve_res = model.solve(solver)

            # 7. Map status
            if hasattr(solve_res, "status"):
                raw_lp = solve_res.status
                raw_sol = 1 if getattr(solve_res, "has_solution", False) else None
            else:
                raw_lp = getattr(model, "status", None)
                raw_sol = getattr(model, "sol_status", None)

            status, message = map_pulp_status(raw_lp, raw_sol)

            # 8. Extract assignments if solution found
            assignments: list[Assignment] = []
            objective_value: float | None = None

            if status in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
                for (i, j, s), var in x.items():
                    val = None
                    if hasattr(var, "value"):
                        val = var.value()
                    elif isinstance(var, pulp.LpVariable):
                        val = pulp.value(var)

                    if val is not None and val >= 0.5:
                        assignments.append(
                            Assignment(
                                employee_id=i,
                                unit_id=j,
                                shift_id=s,
                                hours=shift_durations.get(s, 0.0),
                            )
                        )

                if hasattr(solve_res, "objective") and solve_res.objective is not None:
                    objective_value = float(solve_res.objective)
                elif model.objective is not None:
                    raw_obj = pulp.value(model.objective)
                    objective_value = float(raw_obj) if raw_obj is not None else None

            runtime_seconds = time.perf_counter() - start_time
            return SolveOutcome(
                status=status,
                assignments=assignments,
                objective_value=objective_value,
                runtime_seconds=runtime_seconds,
                message=message,
            )

        except SolverUnavailableError:
            raise
        except Exception as e:
            runtime_seconds = time.perf_counter() - start_time
            return SolveOutcome(
                status=SolverStatus.ERROR,
                assignments=[],
                objective_value=None,
                runtime_seconds=runtime_seconds,
                message=f"MILP solver error: {str(e)}",
            )
