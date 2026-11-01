"""
Replacement Candidate Search Service.
Finds and ranks eligible replacement workers when a worker is absent or a shortage occurs.
"""
from dataclasses import dataclass
from app.domain.models import Scenario, Employee, Shift, ProductionUnit
from app.domain.enums import QualificationPolicy
from app.domain.qualification import is_qualified
from app.domain.temporal import shifts_conflict


@dataclass
class ReplacementCandidate:
    employee_id: str
    employee_name: str
    is_qualified: bool
    is_consenting_overtime: bool
    is_on_call: bool
    current_scheduled_hours: float
    max_allowed_hours: float
    overtime_required: bool
    has_rest_conflict: bool
    suitability_score: float  # Higher is better
    rejection_reason: str | None = None


def find_replacement_candidates(
    scenario: Scenario,
    target_unit_id: str,
    target_shift_id: str,
    currently_assigned_hours: dict[str, float],
    assigned_shifts_by_emp: dict[str, set[str]],
    qualification_policy: QualificationPolicy = QualificationPolicy.LEVEL_AND_CERTIFICATION,
    min_rest_hours: float = 11.0,
) -> list[ReplacementCandidate]:
    """
    Search and rank candidate workers for a shortage cell.
    Considers qualification, current scheduled hours, OT consent, and rest conflicts.
    """
    target_unit = next((u for u in scenario.units if u.id == target_unit_id), None)
    target_shift = next((s for s in scenario.shifts if s.id == target_shift_id), None)
    shift_map = {s.id: s for s in scenario.shifts}

    if not target_unit or not target_shift:
        return []

    candidates: list[ReplacementCandidate] = []

    for emp in scenario.employees:
        # 1. Skip absent employees
        if emp.is_absent:
            continue

        # 2. Check qualification
        qualified = is_qualified(emp, target_unit, qualification_policy)

        # 3. Check already assigned in same shift
        already_in_shift = target_shift_id in assigned_shifts_by_emp.get(emp.id, set())
        if already_in_shift:
            continue

        # 4. Check rest conflicts with other assigned shifts
        rest_conflict = False
        for s_id in assigned_shifts_by_emp.get(emp.id, set()):
            other_s = shift_map.get(s_id)
            if other_s:
                is_conf, _ = shifts_conflict(target_shift, other_s, min_rest_hours=min_rest_hours)
                if is_conf:
                    rest_conflict = True
                    break

        curr_h = currently_assigned_hours.get(emp.id, 0.0)
        needed_h = target_shift.duration_hours
        reg_limit = emp.regular_hours_limit if emp.regular_hours_limit is not None else emp.max_hours
        ot_required = (curr_h + needed_h) > reg_limit
        eff_max = emp.effective_max_hours()
        capacity_exceeded = (curr_h + needed_h) > eff_max

        # Reasons
        rejection = None
        if not qualified:
            rejection = "Lacks required qualifications/certifications"
        elif rest_conflict:
            rejection = "Violates 11-hour minimum rest period"
        elif ot_required and not emp.overtime_opt_in:
            rejection = "Overtime required but worker did not opt in"
        elif capacity_exceeded:
            rejection = "Exceeds maximum allowable hours (including OT cap)"

        # Suitability Score
        score = 0.0
        if qualified and not rest_conflict and not capacity_exceeded and not (ot_required and not emp.overtime_opt_in):
            score += 50.0
            if not ot_required:
                score += 30.0  # Regular hours preferred over OT cost
            elif emp.overtime_opt_in:
                score += 15.0  # Consenting OT is acceptable
            if target_shift_id in emp.on_call_shifts:
                score += 10.0  # Explicitly confirmed on-call
            # Balance workload: prefer worker with fewer hours
            score += max(0.0, 10.0 - (curr_h / 5.0))

        candidates.append(
            ReplacementCandidate(
                employee_id=emp.id,
                employee_name=emp.name,
                is_qualified=qualified,
                is_consenting_overtime=emp.overtime_opt_in,
                is_on_call=target_shift_id in emp.on_call_shifts,
                current_scheduled_hours=curr_h,
                max_allowed_hours=eff_max,
                overtime_required=ot_required,
                has_rest_conflict=rest_conflict,
                suitability_score=score,
                rejection_reason=rejection,
            )
        )

    # Sort candidates by score descending
    candidates.sort(key=lambda c: (-c.suitability_score, c.employee_id))
    return candidates
