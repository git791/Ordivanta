from pathlib import Path
from datetime import datetime
from app.domain.models import Scenario, Employee, ProductionUnit, Shift, Demand
from .base import (
    BaseDatasetLoader,
    DatasetMetadata,
    DatasetType,
    InstanceSummary,
    CompatibilityStatus,
)


class ShiftSchedulingLoader(BaseDatasetLoader):
    """
    Loader for the Shift Scheduling Benchmark Instances (instances1_225).
    Format: Multi-activity shift scheduling with planning horizon, task workstations,
    staff working-hour bounds, and 15-minute interval cover demands.
    """

    def __init__(self, data_dir: Path | None = None):
        self.dataset_id = DatasetType.SHIFT_SCHEDULING.value
        if data_dir is not None:
            self.data_dir = data_dir
        else:
            root = Path(__file__).resolve().parents[3]
            self.data_dir = root / "data" / "instances1_225" / "instances1_225" / "txt"

    def get_metadata(self) -> DatasetMetadata:
        total = len(list(self.data_dir.glob("*.txt"))) if self.data_dir.exists() else 225
        return DatasetMetadata(
            dataset_id=self.dataset_id,
            name="Shift Scheduling Benchmark (instances1_225)",
            category="Supplementary Shift Design Benchmark",
            description=(
                "Multi-activity, multi-task continuous shift scheduling benchmark instances. "
                "Models discrete 15-minute time intervals across multi-day horizons with multiple workstation "
                "tasks and individual employee minimum/maximum scheduled minutes."
            ),
            source_folder="data/instances1_225/instances1_225/txt/",
            file_format="Custom text specification (.txt) with XML roster equivalent (.ros)",
            total_instances=total,
            compatible_instances=total,
            partially_compatible_instances=total,
            unsupported_instances=0,
            fields_available=[
                "SECTION_HORIZON (planning horizon length in days, e.g. 7 or 14)",
                "SECTION_TASKS (number of independent workstations or tasks)",
                "SECTION_STAFF (employee ID, minimum minutes, maximum minutes)",
                "SECTION_COVER (day, 15-minute time slot e.g. 06:00-06:15, task ID, min headcount, max headcount)"
            ],
            mapped_constraints=[
                "Workstation task staffing demand (mapped to Ordivanta Demand using Min requirement)",
                "Workstation task qualification (mapped to unit required_skills and employee skills)",
                "Time slot duration in hours (0.25h for each 15-min interval)",
                "Single task assignment per time slot (sum_j x_{ijs} <= 1)",
                "Maximum working hours limit (MaxTotalMinutes / 60.0 mapped to max_hours)"
            ],
            unsupported_constraints=[
                "MinTotalMinutes (minimum working hours floor)",
                "Max headcount cap in SECTION_COVER (Ordivanta enforces coverage as >= required headcount)",
                "Rest break scheduling rules within continuous shift windows",
                "Task transition/changeover fatigue penalties between consecutive slots"
            ],
            transformation_notes=(
                "Each 15-minute interval is mapped into a discrete Ordivanta Shift. "
                "Each task is mapped into a distinct ProductionUnit. "
                "By default, loads a 1-day or multi-day operational horizon for interactive solving. "
                "Min headcount from SECTION_COVER is mapped to required_headcount."
            ),
        )

    def list_instances(self) -> list[InstanceSummary]:
        if not self.data_dir.exists():
            return []

        # Sort files by complexity: staff count, task count, horizon
        files = sorted(self.data_dir.glob("*.txt"), key=lambda p: (len(p.name), p.name))
        summaries = []

        for p in files:
            instance_id = p.stem.lower()
            try:
                # Parse filename e.g. 1_7_10_1.txt -> index 1, 7 days, 10 staff, 1 task
                parts = p.stem.split("_")
                horizon = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 7
                staff_count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 10
                task_count = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1

                summaries.append(
                    InstanceSummary(
                        instance_id=instance_id,
                        dataset_id=self.dataset_id,
                        name=f"Shift Instance {p.stem} ({staff_count} staff, {task_count} tasks, {horizon}d)",
                        filename=p.name,
                        employee_count=staff_count,
                        unit_count=task_count,
                        shift_count=96 * min(horizon, 1),  # Day 1 operational slots
                        demand_count=96 * task_count * min(horizon, 1),
                        horizon_days=horizon,
                        compatibility_status=CompatibilityStatus.PARTIALLY_COMPATIBLE,
                        supported_constraints=[
                            "Workstation task demand", "Maximum scheduled hours",
                            "Task qualifications", "Single task assignment per slot"
                        ],
                        unsupported_constraints=[
                            "Break placement rules", "Min hours floor", "Overstaffing ceiling"
                        ],
                        notes="Multi-activity 15-minute continuous staffing benchmark."
                    )
                )
            except Exception:
                continue

        return summaries

    def load_instance(self, instance_id: str, max_days: int | None = 1, **kwargs) -> tuple[Scenario, InstanceSummary]:
        target_name = f"{instance_id}.txt"
        file_path = None
        for p in self.data_dir.glob("*.txt"):
            if p.stem.lower() == instance_id.lower() or p.name.lower() == target_name.lower():
                file_path = p
                break

        if not file_path or not file_path.exists():
            raise FileNotFoundError(f"Instance '{instance_id}' not found in {self.data_dir}")

        lines = [l.strip() for l in file_path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("#")]
        sections: dict[str, list[str]] = {}
        curr = None
        for line in lines:
            if line.startswith("SECTION_"):
                curr = line
                sections[curr] = []
            elif curr:
                sections[curr].append(line)

        horizon = int(sections.get("SECTION_HORIZON", ["7"])[0])
        effective_days = min(horizon, max_days) if max_days else horizon
        num_tasks = int(sections.get("SECTION_TASKS", ["1"])[0])

        # Workstation units for each task
        units: list[ProductionUnit] = []
        for t in range(1, num_tasks + 1):
            units.append(
                ProductionUnit(
                    id=f"station_task_{t}",
                    name=f"Workstation Task {t}",
                    required_skills=[f"skill_task_{t}"],
                )
            )

        # Parse cover demands and collect distinct shifts
        shifts_dict: dict[str, Shift] = {}
        demands: list[Demand] = []

        for row in sections.get("SECTION_COVER", []):
            parts = [p.strip() for p in row.split(",")]
            if len(parts) >= 5 and parts[0].isdigit():
                day = int(parts[0])
                time_range = parts[1]
                t_id = int(parts[2])
                min_req = int(parts[3])

                if day <= effective_days:
                    # Parse time range e.g. 06:00-06:15
                    times = time_range.split("-")
                    start_t = times[0].strip() if len(times) > 0 else "06:00"
                    end_t = times[1].strip() if len(times) > 1 else "06:15"

                    shift_id = f"d{day}_{start_t.replace(':', '')}_{end_t.replace(':', '')}"
                    if shift_id not in shifts_dict:
                        shifts_dict[shift_id] = Shift(
                            id=shift_id,
                            name=f"Day {day} [{time_range}]",
                            start_time=start_t,
                            end_time=end_t,
                            duration_hours=0.25,
                        )

                    if min_req > 0:
                        demands.append(
                            Demand(
                                unit_id=f"station_task_{t_id}",
                                shift_id=shift_id,
                                required_headcount=min_req,
                            )
                        )

        shifts = list(shifts_dict.values())
        all_shift_ids = [s.id for s in shifts]

        # Parse staff
        employees: list[Employee] = []
        for row in sections.get("SECTION_STAFF", []):
            parts = [p.strip() for p in row.split(",")]
            if parts and parts[0].isdigit():
                s_id = parts[0]
                max_min = float(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 2400.0

                employees.append(
                    Employee(
                        id=f"worker_{s_id}",
                        name=f"Worker {s_id}",
                        skills=[f"skill_task_{t}" for t in range(1, num_tasks + 1)],
                        available_shifts=all_shift_ids,
                        max_hours=round(max_min / 60.0, 2),
                    )
                )

        scenario = Scenario(
            id=f"ss_{instance_id}",
            name=f"Shift Scheduling {file_path.stem} ({effective_days}d)",
            employees=employees,
            units=units,
            shifts=shifts,
            demands=demands,
            created_at=datetime.utcnow(),
        )

        summary = InstanceSummary(
            instance_id=instance_id,
            dataset_id=self.dataset_id,
            name=scenario.name,
            filename=file_path.name,
            employee_count=len(employees),
            unit_count=len(units),
            shift_count=len(shifts),
            demand_count=len(demands),
            horizon_days=effective_days,
            compatibility_status=CompatibilityStatus.PARTIALLY_COMPATIBLE,
            supported_constraints=[
                "Workstation task demand", "Maximum scheduled hours",
                "Task qualifications", "Single task assignment per slot"
            ],
            unsupported_constraints=[
                "Break placement rules", "Min hours floor", "Overstaffing ceiling"
            ],
            notes="15-minute multi-task shift scheduling benchmark."
        )

        return scenario, summary
