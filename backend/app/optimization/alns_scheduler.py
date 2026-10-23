"""
Adaptive Large Neighbourhood Search (ALNS) Metaheuristic Scheduler.

An experimental iterative optimization method for large-scale workforce scheduling.
ALNS never claims global optimality and strictly outputs FEASIBLE or INFEASIBLE.

Preserves all hard constraints:
1. Demand coverage
2. Qualification (disjunctive rule)
3. Availability
4. At most one assignment per employee per shift
5. Maximum scheduled hours limit
"""
import time
import random
from app.domain.models import Scenario, Assignment
from app.domain.enums import SolverStatus, ObjectivePrimary
from app.domain.temporal import build_shift_conflict_map
from app.schemas.schedule import ObjectiveConfig
from .base import Scheduler, SolveOutcome
from .greedy_scheduler import GreedyScheduler


class ALNSScheduler(Scheduler):
    def __init__(
        self,
        max_iterations: int = 150,
        seed: int = 42,
        cooling_rate: float = 0.98,
    ):
        self.max_iterations = max_iterations
        self.seed = seed
        self.cooling_rate = cooling_rate

    def _evaluate_objective(
        self,
        assignments: list[Assignment],
        scenario: Scenario,
        config: ObjectiveConfig,
    ) -> float:
        """
        Evaluate candidate solution objective identical to MILP formulation.
        Z = Z_hours + w_fairness * Z_fairness + penalty_for_unfilled
        """
        shift_durations = {s.id: s.duration_hours for s in scenario.shifts}
        total_hours = sum(a.hours for a in assignments)

        # Workload fairness deviation
        emp_hours = {e.id: 0.0 for e in scenario.employees}
        for a in assignments:
            emp_hours[a.employee_id] = emp_hours.get(a.employee_id, 0.0) + a.hours

        total_demanded_hours = sum(
            d.required_headcount * shift_durations.get(d.shift_id, 0.0)
            for d in scenario.demands
        )
        total_capacity = sum(e.max_hours for e in scenario.employees)
        if config.proportional_fairness and total_capacity > 0:
            fairness_dev = sum(
                abs(emp_hours[e.id] - (total_demanded_hours * (e.max_hours / total_capacity)))
                for e in scenario.employees
            )
        else:
            target_hours = (
                total_demanded_hours / len(scenario.employees)
                if scenario.employees
                else 0.0
            )
            fairness_dev = sum(abs(h - target_hours) for h in emp_hours.values())

        # Unfilled demand penalty to drive complete coverage
        filled_per_demand: dict[tuple[str, str], int] = {}
        for a in assignments:
            key = (a.unit_id, a.shift_id)
            filled_per_demand[key] = filled_per_demand.get(key, 0) + 1

        unfilled = 0
        for d in scenario.demands:
            key = (d.unit_id, d.shift_id)
            filled = filled_per_demand.get(key, 0)
            unfilled += max(0, d.required_headcount - filled)

        unfilled_penalty = unfilled * 10000.0

        if config.primary == ObjectivePrimary.FAIRNESS:
            return unfilled_penalty + total_hours + fairness_dev
        elif config.primary == ObjectivePrimary.COST:
            w = max(0.0, config.fairness_weight)
            return unfilled_penalty + total_hours + w * fairness_dev
        else:
            return unfilled_penalty + total_hours

    def solve(
        self,
        scenario: Scenario,
        config: ObjectiveConfig,
        time_limit: int | None = None,
    ) -> SolveOutcome:
        start_time = time.perf_counter()
        deadline = start_time + (time_limit or 60)
        rng = random.Random(self.seed)

        # 1. Lookups and constraints structures
        unit_map = {u.id: u for u in scenario.units}
        shift_durations = {s.id: s.duration_hours for s in scenario.shifts}
        emp_map = {e.id: e for e in scenario.employees}
        conflict_map = build_shift_conflict_map(scenario.shifts, min_rest_hours=config.min_rest_hours)

        # Disjunctive qualification lookup
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

        # 2. Generate initial solution using Greedy baseline
        greedy = GreedyScheduler()
        init_outcome = greedy.solve(scenario, config)
        current_assignments = list(init_outcome.assignments)
        current_obj = self._evaluate_objective(current_assignments, scenario, config)

        best_assignments = list(current_assignments)
        best_obj = current_obj

        # Operator definitions and weights
        # Destroy operators:
        # 0: Random removal (10-25% of assignments)
        # 1: Shift-based removal (remove all assignments in 2-4 randomly chosen shifts)
        # 2: Worst-fairness removal (remove assignments from workers with highest hours)
        destroy_weights = [1.0, 1.0, 1.0]

        # Repair operators:
        # 0: Greedy capacity insertion (most remaining hours first)
        # 1: Fairness-seeking insertion (worker farthest below target first)
        repair_weights = [1.0, 1.0]

        total_required_headcount = sum(d.required_headcount for d in scenario.demands)

        iteration = 0
        temperature = 100.0

        while iteration < self.max_iterations and time.perf_counter() < deadline:
            iteration += 1

            # Select operators via roulette wheel
            d_idx = rng.choices(range(3), weights=destroy_weights)[0]
            r_idx = rng.choices(range(2), weights=repair_weights)[0]

            # Work on a copy
            working_assignments = list(current_assignments)

            # --- DESTROY ---
            if d_idx == 0 and working_assignments:
                # Random removal
                remove_count = max(1, int(len(working_assignments) * rng.uniform(0.10, 0.25)))
                indices_to_remove = set(rng.sample(range(len(working_assignments)), k=remove_count))
                working_assignments = [
                    a for idx, a in enumerate(working_assignments) if idx not in indices_to_remove
                ]
            elif d_idx == 1 and working_assignments and scenario.shifts:
                # Shift-based destroy
                n_shifts = max(1, min(len(scenario.shifts), rng.randint(2, 4)))
                chosen_shifts = set(rng.sample([s.id for s in scenario.shifts], k=n_shifts))
                working_assignments = [
                    a for a in working_assignments if a.shift_id not in chosen_shifts
                ]
            elif d_idx == 2 and working_assignments:
                # Over-utilized employee destroy
                emp_hours = {e.id: 0.0 for e in scenario.employees}
                for a in working_assignments:
                    emp_hours[a.employee_id] += a.hours
                sorted_emps = sorted(emp_hours.keys(), key=lambda e: emp_hours[e], reverse=True)
                top_stressed = set(sorted_emps[: max(1, len(sorted_emps) // 4)])
                working_assignments = [
                    a for a in working_assignments if a.employee_id not in top_stressed
                ]

            # --- REPAIR ---
            # Reconstruct assignment counts per demand cell
            filled_per_demand: dict[tuple[str, str], int] = {}
            assigned_shifts: dict[str, set[str]] = {e.id: set() for e in scenario.employees}
            assigned_hours: dict[str, float] = {e.id: 0.0 for e in scenario.employees}

            for a in working_assignments:
                key = (a.unit_id, a.shift_id)
                filled_per_demand[key] = filled_per_demand.get(key, 0) + 1
                assigned_shifts[a.employee_id].add(a.shift_id)
                assigned_hours[a.employee_id] += a.hours

            # Find unfulfilled demands
            missing_demands: list[tuple[str, str, float]] = []
            for d in scenario.demands:
                key = (d.unit_id, d.shift_id)
                needed = d.required_headcount - filled_per_demand.get(key, 0)
                dur = shift_durations.get(d.shift_id, 0.0)
                for _ in range(needed):
                    missing_demands.append((d.unit_id, d.shift_id, dur))

            rng.shuffle(missing_demands)

            total_demanded_hours = sum(
                d.required_headcount * shift_durations.get(d.shift_id, 0.0)
                for d in scenario.demands
            )
            total_capacity = sum(e.max_hours for e in scenario.employees)
            emp_targets: dict[str, float] = {}
            for e in scenario.employees:
                if config.proportional_fairness and total_capacity > 0:
                    emp_targets[e.id] = total_demanded_hours * (e.max_hours / total_capacity)
                else:
                    emp_targets[e.id] = total_demanded_hours / len(scenario.employees) if scenario.employees else 0.0

            for u_id, s_id, dur in missing_demands:
                # Find feasible candidates
                candidates = []
                for emp in scenario.employees:
                    # Hard constraints
                    if s_id not in emp.available_shifts:
                        continue
                    if not qualified[emp.id][u_id]:
                        continue
                    if s_id in assigned_shifts[emp.id]:
                        continue
                    # Temporal conflict check (overlapping shifts or minimum rest violation)
                    if any(assigned_s in conflict_map.get(s_id, set()) for assigned_s in assigned_shifts[emp.id]):
                        continue
                    if assigned_hours[emp.id] + dur > emp.max_hours:
                        continue
                    candidates.append(emp)

                if not candidates:
                    continue

                if r_idx == 0:
                    # Most remaining hours first
                    candidates.sort(
                        key=lambda e: (-(e.max_hours - assigned_hours[e.id]), e.id)
                    )
                else:
                    # Worker closest to or below target hours
                    candidates.sort(
                        key=lambda e: (assigned_hours[e.id] - emp_targets.get(e.id, 0.0), e.id)
                    )

                chosen = candidates[0]
                working_assignments.append(
                    Assignment(
                        employee_id=chosen.id,
                        unit_id=u_id,
                        shift_id=s_id,
                        hours=dur,
                    )
                )
                assigned_shifts[chosen.id].add(s_id)
                assigned_hours[chosen.id] += dur

            # Evaluate new solution
            new_obj = self._evaluate_objective(working_assignments, scenario, config)
            delta = new_obj - current_obj

            # Simulated annealing acceptance criterion
            accept = False
            if delta < 0:
                accept = True
            elif temperature > 1e-4:
                prob = rng.random()
                try:
                    if prob < pow(2.71828, -delta / max(1.0, temperature)):
                        accept = True
                except OverflowError:
                    accept = False

            if accept:
                current_assignments = working_assignments
                current_obj = new_obj
                if new_obj < best_obj:
                    best_assignments = working_assignments
                    best_obj = new_obj
                    destroy_weights[d_idx] += 1.5
                    repair_weights[r_idx] += 1.5
                else:
                    destroy_weights[d_idx] += 0.5
                    repair_weights[r_idx] += 0.5

            temperature *= self.cooling_rate

        runtime_seconds = time.perf_counter() - start_time

        # Status: ALNS is a metaheuristic and cannot prove mathematical optimality or infeasibility
        coverage_count = len(best_assignments)
        is_feasible = (coverage_count >= total_required_headcount)
        if is_feasible:
            status = SolverStatus.FEASIBLE
            msg = f"Feasible schedule found by ALNS ({iteration} iterations, objective: {best_obj:.2f})"
        else:
            status = SolverStatus.NOT_SOLVED
            shortage = total_required_headcount - coverage_count
            msg = (
                f"Heuristic partial schedule: {shortage} positions unfilled after {iteration} iterations "
                f"(ALNS cannot prove mathematical infeasibility)"
            )

        return SolveOutcome(
            status=status,
            assignments=best_assignments,
            objective_value=best_obj,
            runtime_seconds=runtime_seconds,
            message=msg,
        )
