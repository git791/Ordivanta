"""
Deterministic, reproducible manufacturing scenario generator for scalability benchmarking
and realistic workforce disruption experiments.
Uses fixed random seeds and explicit parameter sets.
"""
import math
import random
from datetime import datetime, timezone, timedelta
from app.domain.models import (
    Scenario,
    Employee,
    ProductionUnit,
    Shift,
    Demand,
    SkillRequirement,
    ScenarioGenerationParams,
)


SKILL_POOL = [
    "assembly",
    "machining",
    "welding",
    "inspection",
    "quality_control",
    "packaging",
    "forklift",
    "maintenance",
]

CERTIFICATION_POOL = [
    "iso_9001",
    "six_sigma",
    "forklift_license",
    "first_aid",
    "osha_safety",
]


def generate_manufacturing_scenario(
    scenario_id: str,
    name: str,
    num_employees: int,
    num_units: int,
    horizon_days: int,
    seed: int = 42,
    headcount_per_cell: int = 2,
    max_hours_per_week: float = 40.0,
    ensure_feasible: bool = True,
    # --- Phase 2: Disruption & Realism Extensions ---
    absenteeism_rate: float = 0.0,
    demand_multiplier: float = 1.0,
    enable_voluntary_overtime: bool = False,
    strict_qualifications: bool = False,
    min_rest_hours: float = 0.0,
) -> Scenario:
    """
    Generate a realistic, deterministic manufacturing scenario.

    Parameters:
    - scenario_id: unique identifier
    - name: descriptive title
    - num_employees: total workforce size |I|
    - num_units: number of distinct production workstations |J|
    - horizon_days: days in planning horizon (3 shifts per day: 07:00, 15:00, 23:00)
    - seed: random seed ensuring 100% bitwise reproducibility
    - headcount_per_cell: baseline required headcount per (unit, shift)
    - max_hours_per_week: maximum hours allowed per employee per 7 days
    - ensure_feasible: if True, ensures sufficient qualified, available workforce exists
    - absenteeism_rate: proportion of employees randomly marked absent (e.g. 0.10)
    - demand_multiplier: factor applied to unit-shift demand (e.g. 1.20 for +20%)
    - enable_voluntary_overtime: if True, consenting employees opt in with OT caps
    - strict_qualifications: if True, configures mandatory skill levels & certifications
    - min_rest_hours: minimum rest required between consecutive shifts
    """
    rng = random.Random(seed)

    # 1. Units
    units: list[ProductionUnit] = []
    unit_skills: list[list[str]] = []
    for j in range(num_units):
        u_id = f"unit_{j+1:02d}"
        primary_skill = SKILL_POOL[j % len(SKILL_POOL)]
        skills = [primary_skill]
        if j % 3 == 0:
            sec_skill = SKILL_POOL[(j + 2) % len(SKILL_POOL)]
            skills.append(sec_skill)
        unit_skills.append(skills)

        mandatory_reqs: list[SkillRequirement] = []
        required_certs: list[str] = []
        if strict_qualifications:
            for s in skills:
                # Skill proficiency level 2 or 3
                req_lvl = 3 if s in ("welding", "machining", "quality_control") else 2
                mandatory_reqs.append(SkillRequirement(skill=s, min_level=req_lvl))
            if j % 2 == 0:
                required_certs.append(CERTIFICATION_POOL[j % len(CERTIFICATION_POOL)])

        units.append(
            ProductionUnit(
                id=u_id,
                name=f"Cell {j+1:02d} ({'/'.join(skills)})",
                required_skills=skills,
                mandatory_skill_requirements=mandatory_reqs,
                required_certifications=required_certs,
            )
        )

    # 2. Shifts
    shifts: list[Shift] = []
    shift_defs = [
        ("morning", "07:00", "15:00", 8.0, 0),
        ("afternoon", "15:00", "23:00", 8.0, 0),
        ("night", "23:00", "07:00", 8.0, 1),
    ]
    shift_ids: list[str] = []
    base_date = datetime(2026, 10, 1)
    for day in range(horizon_days):
        day_date = base_date + timedelta(days=day)
        for s_name, start_t, end_t, dur, day_offset in shift_defs:
            s_id = f"d{day+1}_{s_name}"
            shift_ids.append(s_id)
            start_iso = f"{day_date.strftime('%Y-%m-%d')}T{start_t}:00"
            end_iso = f"{(day_date + timedelta(days=day_offset)).strftime('%Y-%m-%d')}T{end_t}:00"
            shifts.append(
                Shift(
                    id=s_id,
                    name=f"Day {day+1} {s_name.capitalize()}",
                    start_time=start_iso,
                    end_time=end_iso,
                    duration_hours=dur,
                )
            )

    # 3. Employees
    horizon_weeks = max(1.0, horizon_days / 7.0)
    emp_regular_h = max_hours_per_week * horizon_weeks

    # Determine absenteeism count
    absent_count = int(round(num_employees * absenteeism_rate))
    absent_indices = set(rng.sample(range(num_employees), k=absent_count)) if absent_count > 0 else set()

    employees: list[Employee] = []
    for i in range(num_employees):
        e_id = f"emp_{i+1:03d}"
        is_absent = i in absent_indices

        # Assign skills
        assigned_skills = set()
        if ensure_feasible:
            target_unit_idx = i % num_units
            assigned_skills.add(unit_skills[target_unit_idx][0])

        extra_count = rng.randint(1, 2)
        for sk in rng.sample(SKILL_POOL, k=extra_count):
            assigned_skills.add(sk)

        # Proficiency levels (1-5) and Certifications
        skill_levels: dict[str, int] = {}
        for s in assigned_skills:
            skill_levels[s] = rng.randint(2, 5) if strict_qualifications else 2

        certs: list[str] = []
        if strict_qualifications:
            # Grant 1-2 certifications
            c_count = rng.randint(1, 2)
            certs = sorted(rng.sample(CERTIFICATION_POOL, k=c_count))

        # Availability
        avail_ratio = rng.uniform(0.80, 0.95) if ensure_feasible else rng.uniform(0.40, 0.60)
        avail_count = max(1, int(len(shift_ids) * avail_ratio))
        avail_shifts = sorted(rng.sample(shift_ids, k=avail_count))

        # Voluntary Overtime & Wages
        # In voluntary OT mode, ~60% of workers opt-in
        ot_opt_in = enable_voluntary_overtime and (rng.random() < 0.60)
        base_rate = round(rng.uniform(22.0, 35.0), 2)
        ot_premium = round(base_rate * 0.5, 2)  # 1.5x time pay = 0.5x additive premium
        max_ot_hours = round(emp_regular_h * 0.25, 1) if ot_opt_in else 0.0

        # On-call
        on_call_list: list[str] = []
        if ot_opt_in and rng.random() < 0.50:
            remaining_shifts = [s for s in shift_ids if s not in avail_shifts]
            if remaining_shifts:
                on_call_list = sorted(rng.sample(remaining_shifts, k=min(len(remaining_shifts), 3)))

        employees.append(
            Employee(
                id=e_id,
                name=f"Worker {i+1:03d}",
                skills=sorted(list(assigned_skills)),
                skill_levels=skill_levels,
                certifications=certs,
                available_shifts=avail_shifts,
                max_hours=round(emp_regular_h, 1),
                is_absent=is_absent,
                absence_reason="Unplanned sick leave" if is_absent else None,
                overtime_opt_in=ot_opt_in,
                regular_hours_limit=round(emp_regular_h, 1),
                max_overtime_hours=max_ot_hours,
                overtime_hourly_premium=ot_premium,
                base_hourly_rate=base_rate,
                on_call_shifts=on_call_list,
                call_in_lead_hours=4.0,
            )
        )

    # 4. Demands with demand_multiplier applied
    demands: list[Demand] = []
    for u in units:
        for s_id in shift_ids:
            # Policy: integer ceiling of demand * multiplier
            final_headcount = max(1, int(math.ceil(headcount_per_cell * demand_multiplier)))
            demands.append(
                Demand(
                    unit_id=u.id,
                    shift_id=s_id,
                    required_headcount=final_headcount,
                    is_critical=(u.id == "unit_01"),
                )
            )

    gen_params = ScenarioGenerationParams(
        seed=seed,
        num_employees=num_employees,
        num_units=num_units,
        horizon_days=horizon_days,
        headcount_per_cell=headcount_per_cell,
        max_hours_per_week=max_hours_per_week,
        absenteeism_rate=absenteeism_rate,
        demand_multiplier=demand_multiplier,
        overtime_enabled=enable_voluntary_overtime,
        strict_qualifications=strict_qualifications,
        min_rest_hours=min_rest_hours,
        qualification_policy="LEVEL_AND_CERTIFICATION" if strict_qualifications else "ANY",
    )

    return Scenario(
        id=scenario_id,
        name=name,
        employees=employees,
        units=units,
        shifts=shifts,
        demands=demands,
        created_at=datetime.now(timezone.utc),
        generation_params=gen_params,
    )
