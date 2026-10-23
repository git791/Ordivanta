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

    Hard Constraints:
    - Coverage: sum_i x_{ijs} >= demand_{js} for all configured (unit, shift) demands.
    - Single Assignment: sum_j x_{ijs} <= 1 for each employee and shift.
    - Max Hours: sum_{j,s} duration_s * x_{ijs} <= max_hours_i for each employee.
    - Availability: x_{ijs} = 0 if shift s is not in employee.available_shifts.
    - Qualification (Disjunctive Rule): x_{ijs} = 0 if unit.required_skills is non-empty
      and the employee has NONE of the unit's required skills.
      Rationale: in manufacturing cells, multiple acceptable skill profiles exist;
      an employee holding any compatible skill is qualified for assignment.

    Mathematical Objectives:
    1. Total Scheduled Hours (Non-Monetary Assignment Efficiency Proxy):
       Z_hours = sum_{i,j,s} h_s * x_{ijs}
       Minimizing Z_hours prevents unnecessary over-allocation and meets demand with
       minimum staffing hours.
    2. Workload Balance / Fairness (Linear Mean Absolute Deviation):
       Target hours H_bar = (sum_{j,s} h_s * d_{js}) / |I|
       u_i >= L_i - H_bar
       u_i >= H_bar - L_i
       Z_fairness = sum_i u_i  (L1 workload deviation across all workers)
    3. Multi-objective Support:
       - Single-stage weighted formulation with explicit dimensional scaling:
         FEASIBILITY: min Z_hours
         COST: min Z_hours + fairness_weight * Z_fairness
         FAIRNESS: min Z_fairness + 0.001 * Z_hours
       - Two-stage optimization (when config.two_stage is True):
         Stage 1: Solve min Z_hours -> H*
         Stage 2: Constrain Z_hours <= H* * (1 + two_stage_tolerance), then solve min Z_fairness.
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

            # Disjunctive qualification rule:
            # Qualified if unit has no skill requirements OR employee possesses at least one required skill
            qualified = {
                e.id: {
                    u.id: (
                        len(u.required_skills) == 0
                        or any(sk in u.required_skills for sk in e.skills)
                    )
                    for u in scenario.units
                }
                for e in scenario.employees
            }

            # 2. Initialize PuLP model
            model = pulp.LpProblem("ordivanta_schedule", pulp.LpMinimize)

            def create_var(name: str, cat: str = "Continuous", low_bound: float | None = None):
                if hasattr(model, "add_variable"):
                    return model.add_variable(name, lowBound=low_bound, cat=cat)
                else:
                    return pulp.LpVariable(name, lowBound=low_bound, cat=cat)

            # 3. Create binary decision variables
            # Only instantiate variable when employee is available and qualified; otherwise set 0
            x: dict[tuple[str, str, str], pulp.LpVariable | int] = {}
            for i in emp_ids:
                for j in unit_ids:
                    for s in shift_ids:
                        if availability[i][s] and qualified[i][j]:
                            var_name = f"x_{i}_{j}_{s}"
                            x[(i, j, s)] = create_var(var_name, cat="Binary")
                        else:
                            x[(i, j, s)] = 0

            # 4. Hard Constraints

            # Coverage: sum_i x_{ijs} >= demand_{js} for all configured demands
            for d in scenario.demands:
                model += (
                    pulp.lpSum(x.get((i, d.unit_id, d.shift_id), 0) for i in emp_ids)
                    >= d.required_headcount,
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
            emp_scheduled_hours: dict[str, pulp.LpAffineExpression] = {}
            for i in emp_ids:
                emp_scheduled_hours[i] = pulp.lpSum(
                    shift_durations.get(s, 0.0) * x.get((i, j, s), 0)
                    for j in unit_ids
                    for s in shift_ids
                    if (i, j, s) in x and isinstance(x[(i, j, s)], pulp.LpVariable)
                )
                model += (
                    emp_scheduled_hours[i] <= emp_max_hours[i],
                    f"max_hours_{i}",
                )

            # 5. Objective terms definition
            # Term A: Total scheduled hours (Non-Monetary Assignment Efficiency Proxy)
            active_vars = [
                (shift_durations.get(s, 0.0), var)
                for (i, j, s), var in x.items()
                if isinstance(var, pulp.LpVariable)
            ]
            total_hours_expr = (
                pulp.lpSum(coeff * var for coeff, var in active_vars)
                if active_vars
                else pulp.LpAffineExpression()
            )

            # Term B: Workload balance / Fairness (Linear absolute deviation)
            total_demanded_hours = sum(
                d.required_headcount * shift_durations.get(d.shift_id, 0.0)
                for d in scenario.demands
            )
            target_hours = (
                total_demanded_hours / len(emp_ids) if len(emp_ids) > 0 else 0.0
            )

            u_fairness: dict[str, pulp.LpVariable] = {}
            for i in emp_ids:
                u_fairness[i] = create_var(f"u_fairness_{i}", low_bound=0.0, cat="Continuous")
                model += (
                    u_fairness[i] >= emp_scheduled_hours[i] - target_hours,
                    f"fairness_pos_{i}",
                )
                model += (
                    u_fairness[i] >= target_hours - emp_scheduled_hours[i],
                    f"fairness_neg_{i}",
                )

            fairness_expr = (
                pulp.lpSum(u_fairness[i] for i in emp_ids)
                if emp_ids
                else pulp.LpAffineExpression()
            )

            # 6. Apply Objective Configuration
            solver = get_solver(time_limit=time_limit)

            if config.two_stage and len(scenario.demands) > 0:
                # Stage 1: Solve for minimum total scheduled hours
                model.setObjective(total_hours_expr)
                stage1_res = model.solve(solver)
                st1_lp = getattr(stage1_res, "status", getattr(model, "status", None))
                st1_sol = (
                    1
                    if getattr(stage1_res, "has_solution", False)
                    else getattr(model, "sol_status", None)
                )
                status1, _ = map_pulp_status(st1_lp, st1_sol)

                if status1 in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
                    opt_hours = pulp.value(total_hours_expr)
                    if opt_hours is not None:
                        allowed_hours = opt_hours * (1.0 + max(0.0, config.two_stage_tolerance))
                        model += (
                            total_hours_expr <= allowed_hours,
                            "stage2_hours_ceiling",
                        )
                    # Stage 2: Minimize workload deviation subject to hours ceiling
                    model.setObjective(fairness_expr + 0.0001 * total_hours_expr)
                    solve_res = model.solve(solver)
                else:
                    solve_res = stage1_res
            else:
                # Single-stage formulation
                if config.primary == ObjectivePrimary.FAIRNESS:
                    # Primary: Workload fairness balanced with assignment efficiency
                    # Prevents wasteful overstaffing while optimizing workload equity
                    model.setObjective(total_hours_expr + fairness_expr)
                elif config.primary == ObjectivePrimary.COST:
                    # Primary: Total scheduled hours + user-specified fairness weight
                    w_fairness = max(0.0, config.fairness_weight)
                    model.setObjective(total_hours_expr + w_fairness * fairness_expr)
                else:
                    # Default: FEASIBILITY (minimizes unnecessary scheduled hours)
                    model.setObjective(total_hours_expr)

                solve_res = model.solve(solver)

            # 7. Map status
            if hasattr(solve_res, "status"):
                raw_lp = solve_res.status
                raw_sol = 1 if getattr(solve_res, "has_solution", False) else None
            else:
                raw_lp = getattr(model, "status", None)
                raw_sol = getattr(model, "sol_status", None)

            status, message = map_pulp_status(raw_lp, raw_sol)

            # Capture solver bound and optimality gap if available
            if hasattr(solve_res, "best_bound") and solve_res.best_bound is not None:
                gap_val = getattr(solve_res, "gap_rel", None)
                gap_str = f", gap: {gap_val*100:.2f}%" if gap_val is not None else ""
                bound_info = f"bound: {solve_res.best_bound:.2f}{gap_str}"
                message = f"{message} ({bound_info})" if message else bound_info

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
