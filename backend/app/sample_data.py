from datetime import datetime
from app.domain.models import Employee, ProductionUnit, Shift, Demand, Scenario


def get_sample_scenario() -> Scenario:
    """Return a realistic, satisfiable sample scenario for manufacturing operations."""
    employees = [
        Employee(
            id="emp_01",
            name="Alice Martin",
            skills=["assembly"],
            available_shifts=["shift_morning", "shift_afternoon"],
            max_hours=24.0,
        ),
        Employee(
            id="emp_02",
            name="Bob Chen",
            skills=["assembly"],
            available_shifts=["shift_morning", "shift_afternoon", "shift_night"],
            max_hours=24.0,
        ),
        Employee(
            id="emp_03",
            name="Carlos Diaz",
            skills=["assembly", "quality_control"],
            available_shifts=["shift_morning", "shift_afternoon", "shift_night"],
            max_hours=24.0,
        ),
        Employee(
            id="emp_04",
            name="Dana White",
            skills=["assembly", "packaging"],
            available_shifts=["shift_morning", "shift_afternoon", "shift_night"],
            max_hours=24.0,
        ),
        Employee(
            id="emp_05",
            name="Elena Rossi",
            skills=["quality_control", "inspection"],
            available_shifts=["shift_afternoon", "shift_night"],
            max_hours=24.0,
        ),
        Employee(
            id="emp_06",
            name="Frank Miller",
            skills=["quality_control", "assembly"],
            available_shifts=["shift_morning", "shift_afternoon", "shift_night"],
            max_hours=24.0,
        ),
        Employee(
            id="emp_07",
            name="Grace Hopper",
            skills=["inspection", "packaging"],
            available_shifts=["shift_morning", "shift_afternoon", "shift_night"],
            max_hours=24.0,
        ),
        Employee(
            id="emp_08",
            name="Hassan Ali",
            skills=["packaging", "forklift"],
            available_shifts=["shift_morning", "shift_night"],
            max_hours=24.0,
        ),
        Employee(
            id="emp_09",
            name="Ivy Taylor",
            skills=["packaging", "forklift"],
            available_shifts=["shift_morning", "shift_afternoon", "shift_night"],
            max_hours=24.0,
        ),
        Employee(
            id="emp_10",
            name="Jack Brown",
            skills=["forklift", "assembly", "quality_control"],
            available_shifts=["shift_morning", "shift_afternoon", "shift_night"],
            max_hours=24.0,
        ),
    ]

    units = [
        ProductionUnit(
            id="unit_assembly",
            name="Assembly Line A",
            required_skills=["assembly"],
        ),
        ProductionUnit(
            id="unit_qc",
            name="Quality Control",
            required_skills=["quality_control", "inspection"],
        ),
        ProductionUnit(
            id="unit_packaging",
            name="Packaging",
            required_skills=["packaging", "forklift"],
        ),
    ]

    shifts = [
        Shift(
            id="shift_morning",
            name="Morning",
            start_time="07:00",
            end_time="15:00",
            duration_hours=8.0,
        ),
        Shift(
            id="shift_afternoon",
            name="Afternoon",
            start_time="15:00",
            end_time="23:00",
            duration_hours=8.0,
        ),
        Shift(
            id="shift_night",
            name="Night",
            start_time="23:00",
            end_time="07:00",
            duration_hours=8.0,
        ),
    ]

    demands = [
        Demand(unit_id="unit_assembly", shift_id="shift_morning", required_headcount=3),
        Demand(unit_id="unit_assembly", shift_id="shift_afternoon", required_headcount=3),
        Demand(unit_id="unit_assembly", shift_id="shift_night", required_headcount=3),
        Demand(unit_id="unit_qc", shift_id="shift_morning", required_headcount=3),
        Demand(unit_id="unit_qc", shift_id="shift_afternoon", required_headcount=3),
        Demand(unit_id="unit_qc", shift_id="shift_night", required_headcount=3),
        Demand(unit_id="unit_packaging", shift_id="shift_morning", required_headcount=3),
        Demand(unit_id="unit_packaging", shift_id="shift_afternoon", required_headcount=3),
        Demand(unit_id="unit_packaging", shift_id="shift_night", required_headcount=3),
    ]

    return Scenario(
        id="scenario_sample",
        name="Standard Manufacturing Facility (Sample)",
        employees=employees,
        units=units,
        shifts=shifts,
        demands=demands,
        created_at=datetime.utcnow(),
    )
