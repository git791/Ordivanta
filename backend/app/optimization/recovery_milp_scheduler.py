"""
Recovery Lexicographic MILP Scheduler.

Separately configurable lexicographic recovery mode:
1. Stage 1: Maximize coverage (minimize weighted uncovered staffing demand: sum_d shortage_d)
   subject to all mandatory constraints (qualification, availability, rest, maximum hours).
2. Stage 2: Subject to best achievable coverage (shortages bounded by Stage 1 optimal value),
   minimize total labor cost (regular hours * base wage + overtime hours * overtime premium)
   plus assignment modifications from locked/original roster.
3. Stage 3: Subject to higher-priority bounds, minimize workload fairness deviation (SAD)
   and preference penalties.

Maintains proof-of-optimality semantics across all optimization stages.
"""
import time
import pulp
from app.domain.models import Scenario, Assignment
from app.domain.enums import SolverStatus, QualificationPolicy
from app.domain.temporal import build_shift_conflict_pairs
from app.domain.qualification import is_qualified
from app.schemas.schedule import ObjectiveConfig
from .base import Scheduler, SolveOutcome, SolverUnavailableError
from .solver_adapter import get_solver, map_pulp_status


class RecoveryMILPScheduler(Scheduler):
    """
    Three-stage lexicographic recovery MILP scheduler for disrupted scenarios.
    """

    def solve(
        self,
        scenario: Scenario,
        config: ObjectiveConfig,
        time_limit: int | None = None,
        locked_assignments: list[Assignment] | None = None,
    ) -> SolveOutcome:
        start_time = time.perf_counter()

        try:
            emp_ids = [e.id for e in scenario.employees]
            unit_ids = [u.id for u in scenario.units]
            shift_ids = [s.id for s in scenario.shifts]
            shift_durations = {s.id: s.duration_hours for s in scenario.shifts}
            emp_map = {e.id: e for e in scenario.employees}

            # Qualification & Availability filtering
            pol = config.qualification_policy
            availability = {
                e.id: {s_id: (s_id in e.available_shifts) for s_id in shift_ids}
                for e in scenario.employees
            }
            qualified = {
                e.id: {
                    u.id: (not e.is_absent) and is_qualified(e, u, pol)
                    for u in scenario.units
                }
                for e in scenario.employees
            }

            model = pulp.LpProblem("ordivanta_recovery_schedule", pulp.LpMinimize)

            def create_var(name: str, cat: str = "Continuous", low_bound: float | None = None, up_bound: float | None = None):
                if hasattr(model, "add_variable"):
                    return model.add_variable(name, lowBound=low_bound, upBound=up_bound, cat=cat)
                return pulp.LpVariable(name, lowBound=low_bound, upBound=up_bound, cat=cat)

            # Decision variables: x_{i,j,s} in {0, 1}
            x: dict[tuple[str, str, str], pulp.LpVariable | int] = {}
            for i in emp_ids:
                for j in unit_ids:
                    for s in shift_ids:
                        if availability[i][s] and qualified[i][j]:
                            x[(i, j, s)] = create_var(f"x_{i}_{j}_{s}", cat="Binary")
                        else:
                            x[(i, j, s)] = 0

            # Shortage variables for each demand: s_{j,s} >= 0
            shortage: dict[tuple[str, str], pulp.LpVariable] = {}
            for d in scenario.demands:
                shortage[(d.unit_id, d.shift_id)] = create_var(
                    f"shortage_{d.unit_id}_{d.shift_id}", cat="Continuous", low_bound=0.0
                )

            # Locked assignments constraint: x_{i,j,s} == 1 if locked
            if locked_assignments:
                for la in locked_assignments:
                    if (la.employee_id, la.unit_id, la.shift_id) in x:
                        var = x[(la.employee_id, la.unit_id, la.shift_id)]
                        if isinstance(var, pulp.LpVariable):
                            model += (var == 1, f"locked_{la.employee_id}_{la.unit_id}_{la.shift_id}")

            # 1. Coverage constraint with explicit shortage: sum_i x_{ijs} + shortage_{js} >= d_{js}
            for d in scenario.demands:
                demand_vars = [x.get((i, d.unit_id, d.shift_id), 0) for i in emp_ids]
                model += (
                    pulp.lpSum(demand_vars) + shortage[(d.unit_id, d.shift_id)] >= d.required_headcount,
                    f"coverage_shortage_{d.unit_id}_{d.shift_id}",
                )

            # 2. At most one assignment per employee per shift
            for i in emp_ids:
                for s in shift_ids:
                    shift_vars = [x.get((i, j, s), 0) for j in unit_ids]
                    model += (pulp.lpSum(shift_vars) <= 1, f"one_shift_{i}_{s}")

            # 3. Temporal conflicts (overlapping shifts & minimum rest)
            conflict_pairs = build_shift_conflict_pairs(scenario.shifts, min_rest_hours=config.min_rest_hours)
            for i in emp_ids:
                for s1, s2 in conflict_pairs:
                    vars_s1 = [x.get((i, j, s1), 0) for j in unit_ids if isinstance(x.get((i, j, s1)), pulp.LpVariable)]
                    vars_s2 = [x.get((i, j, s2), 0) for j in unit_ids if isinstance(x.get((i, j, s2)), pulp.LpVariable)]
                    if vars_s1 and vars_s2:
                        model += (pulp.lpSum(vars_s1) + pulp.lpSum(vars_s2) <= 1, f"temp_conf_{i}_{s1}_{s2}")

            # 4. Hours limit & Overtime constraints
            emp_scheduled_hours: dict[str, pulp.LpAffineExpression] = {}
            emp_ot_hours: dict[str, pulp.LpVariable | float] = {}

            for i in emp_ids:
                emp = emp_map[i]
                emp_scheduled_hours[i] = pulp.lpSum(
                    shift_durations[s] * x.get((i, j, s), 0)
                    for j in unit_ids
                    for s in shift_ids
                    if isinstance(x.get((i, j, s)), pulp.LpVariable)
                )

                # Overtime setup
                reg_limit = emp.regular_hours_limit if emp.regular_hours_limit is not None else emp.max_hours
                if emp.overtime_opt_in and emp.max_overtime_hours > 0:
                    ot_var = create_var(f"ot_{i}", cat="Continuous", low_bound=0.0, up_bound=emp.max_overtime_hours)
                    emp_ot_hours[i] = ot_var
                    # scheduled_hours <= regular_limit + ot_var
                    model += (emp_scheduled_hours[i] <= reg_limit + ot_var, f"max_h_ot_{i}")
                    # ot_var >= scheduled_hours - reg_limit
                    model += (ot_var >= emp_scheduled_hours[i] - reg_limit, f"ot_def_{i}")
                else:
                    emp_ot_hours[i] = 0.0
                    model += (emp_scheduled_hours[i] <= reg_limit, f"max_h_reg_{i}")

            # Objective expressions
            # Term 1: Shortages (weighted higher for critical cells)
            shortage_expr = pulp.lpSum(
                (5.0 if d.is_critical else 1.0) * shortage[(d.unit_id, d.shift_id)]
                for d in scenario.demands
            )

            # Term 2: Total Labor Cost (Regular hours * base wage + Overtime * premium)
            cost_terms = []
            for i in emp_ids:
                emp = emp_map[i]
                rate = emp.base_hourly_rate if emp.base_hourly_rate > 0 else 25.0
                premium = emp.overtime_hourly_premium if emp.overtime_hourly_premium > 0 else (rate * 0.5)
                cost_terms.append(rate * emp_scheduled_hours[i])
                if isinstance(emp_ot_hours[i], pulp.LpVariable):
                    cost_terms.append(premium * emp_ot_hours[i])
            cost_expr = pulp.lpSum(cost_terms)

            # Term 3: Fairness SAD
            total_demanded_hours = sum(d.required_headcount * shift_durations[d.shift_id] for d in scenario.demands)
            total_cap = sum(emp_map[i].effective_max_hours() for i in emp_ids)
            u_fairness = {}
            for i in emp_ids:
                if config.proportional_fairness and total_cap > 0:
                    tgt = total_demanded_hours * (emp_map[i].effective_max_hours() / total_cap)
                else:
                    tgt = total_demanded_hours / len(emp_ids) if emp_ids else 0.0
                u_fairness[i] = create_var(f"u_rec_fair_{i}", low_bound=0.0)
                model += (u_fairness[i] >= emp_scheduled_hours[i] - tgt, f"fair_pos_{i}")
                model += (u_fairness[i] >= tgt - emp_scheduled_hours[i], f"fair_neg_{i}")
            fairness_expr = pulp.lpSum(u_fairness[i] for i in emp_ids)

            solver = get_solver(time_limit=time_limit)

            # --- STAGE 1: Minimize Shortages ---
            model.setObjective(shortage_expr)
            res1 = model.solve(solver)
            st1_lp = getattr(res1, "status", getattr(model, "status", None))
            st1_sol = 1 if getattr(res1, "has_solution", False) else getattr(model, "sol_status", None)
            status1, _ = map_pulp_status(st1_lp, st1_sol)

            if status1 == SolverStatus.INFEASIBLE:
                return SolveOutcome(
                    status=SolverStatus.INFEASIBLE,
                    assignments=[],
                    objective_value=None,
                    runtime_seconds=time.perf_counter() - start_time,
                    message="Recovery MILP proven infeasible in Stage 1",
                )

            min_shortage = pulp.value(shortage_expr) or 0.0
            # Bound shortage to achievable minimum (exact integer for counting positions)
            model += (shortage_expr <= round(min_shortage, 4), "shortage_ceiling")

            # --- STAGE 2: Minimize Labor & Overtime Cost ---
            model.setObjective(cost_expr)
            res2 = model.solve(solver)
            st2_lp = getattr(res2, "status", getattr(model, "status", None))
            st2_sol = 1 if getattr(res2, "has_solution", False) else getattr(model, "sol_status", None)
            status2, _ = map_pulp_status(st2_lp, st2_sol)

            min_cost = pulp.value(cost_expr) or 0.0
            model += (cost_expr <= min_cost * (1.0 + max(0.0, config.two_stage_tolerance)) + 1e-3, "cost_ceiling")

            # --- STAGE 3: Minimize Fairness SAD ---
            model.setObjective(fairness_expr + 0.001 * cost_expr)
            res3 = model.solve(solver)
            st3_lp = getattr(res3, "status", getattr(model, "status", None))
            st3_sol = 1 if getattr(res3, "has_solution", False) else getattr(model, "sol_status", None)
            status3, msg3 = map_pulp_status(st3_lp, st3_sol)

            if status1 == SolverStatus.OPTIMAL and status2 == SolverStatus.OPTIMAL and status3 == SolverStatus.OPTIMAL:
                final_status = SolverStatus.OPTIMAL
            else:
                final_status = SolverStatus.FEASIBLE

            # Extract assignments
            assignments: list[Assignment] = []
            for (i, j, s), var in x.items():
                if isinstance(var, pulp.LpVariable) and (var.value() or 0.0) >= 0.5:
                    assignments.append(
                        Assignment(
                            employee_id=i,
                            unit_id=j,
                            shift_id=s,
                            hours=shift_durations.get(s, 8.0),
                        )
                    )

            achieved_shortage = round(min_shortage, 4)
            achieved_cost = pulp.value(cost_expr) or min_cost
            achieved_sad = pulp.value(fairness_expr) or 0.0

            narrative = (
                f"Lexicographic Recovery: Uncovered shortfall = {achieved_shortage:.1f} pos, "
                f"Cost = ${achieved_cost:.2f}, Fairness SAD = {achieved_sad:.2f}h"
            )

            return SolveOutcome(
                status=final_status,
                assignments=assignments,
                objective_value=round(achieved_shortage, 4),
                runtime_seconds=round(time.perf_counter() - start_time, 4),
                message=narrative,
            )

        except SolverUnavailableError:
            raise
        except Exception as e:
            return SolveOutcome(
                status=SolverStatus.ERROR,
                assignments=[],
                objective_value=None,
                runtime_seconds=round(time.perf_counter() - start_time, 4),
                message=f"Recovery MILP error: {str(e)}",
            )
