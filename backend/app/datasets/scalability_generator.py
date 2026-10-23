"""
Deterministic, reproducible manufacturing scenario generator for scalability benchmarking.
Uses fixed random seeds and explicit parameter sets.
"""
import random
from datetime import datetime, timezone, timedelta
from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand


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
    - headcount_per_cell: required headcount per (unit, shift)
    - max_hours_per_week: maximum hours allowed per employee per 7 days
    - ensure_feasible: if True, ensures sufficient qualified, available workforce exists
    """
    rng = random.Random(seed)

    # 1. Units
    units: list[ProductionUnit] = []
    unit_skills: list[list[str]] = []
    for j in range(num_units):
        u_id = f"unit_{j+1:02d}"
        # Each unit has 1 primary skill, and every third has a secondary skill
        primary_skill = SKILL_POOL[j % len(SKILL_POOL)]
        skills = [primary_skill]
        if j % 3 == 0:
            sec_skill = SKILL_POOL[(j + 2) % len(SKILL_POOL)]
            skills.append(sec_skill)
        unit_skills.append(skills)
        units.append(
            ProductionUnit(
                id=u_id,
                name=f"Cell {j+1:02d} ({'/'.join(skills)})",
                required_skills=skills,
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
    emp_max_h = max_hours_per_week * horizon_weeks

    employees: list[Employee] = []
    for i in range(num_employees):
        e_id = f"emp_{i+1:03d}"

        # Assign core skills to guarantee qualification coverage across all units
        assigned_skills = set()
        if ensure_feasible:
            # Guarantee every unit has workers qualified for it
            target_unit_idx = i % num_units
            assigned_skills.add(unit_skills[target_unit_idx][0])

        # Add 1-2 additional random skills for flexibility
        extra_count = rng.randint(1, 2)
        for sk in rng.sample(SKILL_POOL, k=extra_count):
            assigned_skills.add(sk)

        # Availability: available for 80% to 95% of shifts
        avail_ratio = rng.uniform(0.80, 0.95) if ensure_feasible else rng.uniform(0.40, 0.60)
        avail_count = max(1, int(len(shift_ids) * avail_ratio))
        avail_shifts = sorted(rng.sample(shift_ids, k=avail_count))

        employees.append(
            Employee(
                id=e_id,
                name=f"Worker {i+1:03d}",
                skills=sorted(list(assigned_skills)),
                available_shifts=avail_shifts,
                max_hours=round(emp_max_h, 1),
            )
        )

    # 4. Demands
    demands: list[Demand] = []
    for u in units:
        for s_id in shift_ids:
            demands.append(
                Demand(
                    unit_id=u.id,
                    shift_id=s_id,
                    required_headcount=headcount_per_cell,
                )
            )

    return Scenario(
        id=scenario_id,
        name=name,
        employees=employees,
        units=units,
        shifts=shifts,
        demands=demands,
        created_at=datetime.now(timezone.utc),
    )
