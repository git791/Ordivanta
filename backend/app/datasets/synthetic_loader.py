from pathlib import Path
from datetime import datetime
from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand
from app.sample_data import get_sample_scenario
from .base import (
    BaseDatasetLoader,
    DatasetMetadata,
    DatasetType,
    InstanceSummary,
    CompatibilityStatus,
)


class SyntheticManufacturingLoader(BaseDatasetLoader):
    """
    Primary Synthetic Manufacturing Dataset Loader.
    Provides reproducible, ground-truth industrial scenarios with employees,
    skills, availability, shift durations, unit demands, and working-hour caps.
    """

    def __init__(self):
        self.dataset_id = DatasetType.SYNTHETIC_MANUFACTURING.value

    def get_metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            dataset_id=self.dataset_id,
            name="Ordivanta Synthetic Manufacturing Benchmark (Primary)",
            category="Primary Synthetic Manufacturing Dataset",
            description=(
                "Primary reproducible manufacturing plant dataset designed for Ordivanta decision support. "
                "Simulates multi-station assembly, quality control, and packaging shifts with strict qualification, "
                "availability windows, and maximum working hour constraints. Labeled strictly as synthetic data."
            ),
            source_folder="backend/app/sample_data.py",
            file_format="Native Python domain structure / JSON",
            total_instances=3,
            compatible_instances=3,
            partially_compatible_instances=0,
            unsupported_instances=0,
            fields_available=[
                "employee.id", "employee.name", "employee.skills", "employee.available_shifts",
                "employee.max_hours", "unit.id", "unit.name", "unit.required_skills",
                "shift.id", "shift.name", "shift.start_time", "shift.end_time", "shift.duration_hours",
                "demand.unit_id", "demand.shift_id", "demand.required_headcount"
            ],
            mapped_constraints=[
                "Station staffing coverage (sum_i x_{ijs} >= d_{js})",
                "Employee availability by shift (x_{ijs} <= a_{is})",
                "Workstation qualification match (x_{ijs} <= q_{ij})",
                "Single station assignment per shift (sum_j x_{ijs} <= 1)",
                "Maximum scheduled hours limit (sum_{j,s} h_s x_{ijs} <= H_i)"
            ],
            unsupported_constraints=[],
            transformation_notes=(
                "Ground-truth primary reference dataset. No lossy transformation applied. "
                "All constraints represent 100% native hard constraints in the MILP formulation."
            ),
        )

    def list_instances(self) -> list[InstanceSummary]:
        return [
            InstanceSummary(
                instance_id="mfg_standard_sample",
                dataset_id=self.dataset_id,
                name="Standard Manufacturing Facility (10 staff, 3 units, 3 shifts)",
                filename="sample_data.py::get_sample_scenario",
                employee_count=10,
                unit_count=3,
                shift_count=3,
                demand_count=9,
                horizon_days=1,
                compatibility_status=CompatibilityStatus.COMPATIBLE,
                supported_constraints=[
                    "Headcount coverage", "Qualifications", "Shift availability",
                    "Single assignment per shift", "Maximum hours (24h/wk)"
                ],
                unsupported_constraints=[],
                notes="Primary baseline scenario. 100% solvable with OPTIMAL MILP status."
            ),
            InstanceSummary(
                instance_id="mfg_high_demand_feasible",
                dataset_id=self.dataset_id,
                name="High-Utilization Line (12 staff, 3 units, 3 shifts)",
                filename="synthetic_generator",
                employee_count=12,
                unit_count=3,
                shift_count=3,
                demand_count=9,
                horizon_days=1,
                compatibility_status=CompatibilityStatus.COMPATIBLE,
                supported_constraints=[
                    "Headcount coverage", "Qualifications", "Shift availability",
                    "Single assignment per shift", "Maximum hours"
                ],
                unsupported_constraints=[],
                notes="Tight staffing ratio testing boundary capacity."
            ),
            InstanceSummary(
                instance_id="mfg_shortage_infeasible",
                dataset_id=self.dataset_id,
                name="Deficit Scenario (Understaffed QC - Provably Infeasible)",
                filename="synthetic_generator",
                employee_count=6,
                unit_count=3,
                shift_count=3,
                demand_count=9,
                horizon_days=1,
                compatibility_status=CompatibilityStatus.COMPATIBLE,
                supported_constraints=[
                    "Headcount coverage", "Qualifications", "Shift availability",
                    "Single assignment per shift", "Maximum hours"
                ],
                unsupported_constraints=[],
                notes="Explicit shortage benchmark to verify truthful INFEASIBLE reporting."
            )
        ]

    def load_instance(self, instance_id: str, **kwargs) -> tuple[Scenario, InstanceSummary]:
        summaries = {s.instance_id: s for s in self.list_instances()}
        summary = summaries.get(instance_id) or summaries["mfg_standard_sample"]

        if instance_id == "mfg_shortage_infeasible":
            # Scenario with 6 workers and 27 required headcount -> mathematically infeasible
            base = get_sample_scenario()
            scenario = Scenario(
                id=instance_id,
                name="Deficit Scenario (Understaffed QC - Provably Infeasible)",
                employees=base.employees[:6],
                units=base.units,
                shifts=base.shifts,
                demands=base.demands,
                created_at=datetime.utcnow()
            )
        elif instance_id == "mfg_high_demand_feasible":
            base = get_sample_scenario()
            extra_emps = [
                Employee(id="emp_11", name="Kevin Zhang", skills=["assembly", "packaging"], available_shifts=["shift_morning", "shift_afternoon", "shift_night"], max_hours=24.0),
                Employee(id="emp_12", name="Laura Gomez", skills=["quality_control", "inspection"], available_shifts=["shift_morning", "shift_afternoon", "shift_night"], max_hours=24.0),
            ]
            scenario = Scenario(
                id=instance_id,
                name="High-Utilization Line (12 staff, 3 units, 3 shifts)",
                employees=base.employees + extra_emps,
                units=base.units,
                shifts=base.shifts,
                demands=base.demands,
                created_at=datetime.utcnow()
            )
        else:
            scenario = get_sample_scenario()
            scenario.id = instance_id

        return scenario, summary
