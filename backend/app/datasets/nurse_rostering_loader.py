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


class NurseRosteringLoader(BaseDatasetLoader):
    """
    Loader for the Nurse Rostering Benchmark Instances (instances1_24).
    Format: INRC-II / Nottingham NRP with horizon, shifts, staff constraints,
    days off, and shift cover requirements.
    """

    def __init__(self, data_dir: Path | None = None):
        self.dataset_id = DatasetType.NURSE_ROSTERING.value
        if data_dir is not None:
            self.data_dir = data_dir
        else:
            # Find data directory relative to repository root
            root = Path(__file__).resolve().parents[3]
            self.data_dir = root / "data" / "instances1_24" / "instances1_24"

    def get_metadata(self) -> DatasetMetadata:
        total = len(list(self.data_dir.glob("*.txt"))) if self.data_dir.exists() else 24
        return DatasetMetadata(
            dataset_id=self.dataset_id,
            name="Nurse Rostering Benchmark (instances1_24)",
            category="Supplementary Healthcare Benchmark",
            description=(
                "International Nurse Rostering Competition (INRC / Nottingham) benchmark instances. "
                "Covers 14 to 28-day hospital ward rostering with multi-shift staffing, individual employee "
                "availability, days-off restrictions, and shift duration limits."
            ),
            source_folder="data/instances1_24/instances1_24/",
            file_format="NRP text specification (.txt) and XML roster (.ros)",
            total_instances=total,
            compatible_instances=total,
            partially_compatible_instances=total,
            unsupported_instances=0,
            fields_available=[
                "SECTION_HORIZON (planning horizon length in days)",
                "SECTION_SHIFTS (shift ID, duration in minutes, forbidden sequences)",
                "SECTION_STAFF (max shifts, max/min total minutes, max/min consecutive shifts, days off, max weekends)",
                "SECTION_DAYS_OFF (mandatory day-off calendar per employee)",
                "SECTION_SHIFT_ON_REQUESTS (employee shift preferences)",
                "SECTION_SHIFT_OFF_REQUESTS (employee avoidance preferences)",
                "SECTION_COVER (daily shift staffing requirement and penalty weights)"
            ],
            mapped_constraints=[
                "Daily ward shift staffing demand (mapped to Ordivanta Demand)",
                "Employee mandatory days off (mapped to available_shifts exclusion)",
                "Shift length in hours (mapped to Shift.duration_hours)",
                "Single shift per day assignment (sum_j x_{ijs} <= 1)",
                "Maximum working hours limit (MaxTotalMinutes / 60.0 mapped to max_hours)",
                "Specific shift disqualifications (e.g. L=0 in MaxShifts)"
            ],
            unsupported_constraints=[
                "MinTotalMinutes (minimum hours floor)",
                "MinConsecutiveShifts / MaxConsecutiveShifts (consecutive work stretch limits)",
                "MinConsecutiveDaysOff (minimum rest block length)",
                "MaxWeekends (weekend shift limits)",
                "Forbidden shift sequences (e.g. night shift immediately followed by morning)",
                "Soft shift on/off preference request weights (penalties in objective)",
                "Soft under/over staffing penalties (Ordivanta treats required cover as a hard requirement)"
            ],
            transformation_notes=(
                "Each (Day, ShiftID) is mapped into a discrete Ordivanta Shift instance. "
                "Hospital ward is mapped to an operational ProductionUnit ('unit_ward'). "
                "Nurses are mapped to Employees with 'nursing' qualification. "
                "Unsupported sequence, weekend, and soft penalty rules are flagged as partially compatible."
            ),
        )

    def list_instances(self) -> list[InstanceSummary]:
        if not self.data_dir.exists():
            return []

        files = sorted(self.data_dir.glob("*.txt"), key=lambda p: int("".join(filter(str.isdigit, p.stem)) or 0))
        summaries = []

        for p in files:
            instance_id = p.stem.lower()
            try:
                # Fast header inspection
                lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("#")]
                horizon = 14
                staff_count = 0
                shift_count = 1
                demand_rows = 0

                curr = None
                for line in lines:
                    if line.startswith("SECTION_"):
                        curr = line
                    elif curr == "SECTION_HORIZON":
                        horizon = int(line)
                    elif curr == "SECTION_SHIFTS":
                        shift_count += 1
                    elif curr == "SECTION_STAFF":
                        staff_count += 1
                    elif curr == "SECTION_COVER":
                        demand_rows += 1

                summaries.append(
                    InstanceSummary(
                        instance_id=instance_id,
                        dataset_id=self.dataset_id,
                        name=f"Nurse Rostering {p.stem} ({staff_count} nurses, {horizon} days)",
                        filename=p.name,
                        employee_count=staff_count,
                        unit_count=1,
                        shift_count=shift_count * min(horizon, 14),
                        demand_count=demand_rows,
                        horizon_days=horizon,
                        compatibility_status=CompatibilityStatus.PARTIALLY_COMPATIBLE,
                        supported_constraints=[
                            "Staffing headcount demand", "Max hours limit",
                            "Mandatory days off", "Single shift assignment per day"
                        ],
                        unsupported_constraints=[
                            "Consecutive shift limits", "Min hours limit",
                            "Weekend limits", "Shift transition rules"
                        ],
                        notes="Multi-day hospital ward rostering with individual availability and duration caps."
                    )
                )
            except Exception:
                continue

        return summaries

    def load_instance(self, instance_id: str, max_days: int | None = 14, **kwargs) -> tuple[Scenario, InstanceSummary]:
        # Locate file
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

        horizon = int(sections.get("SECTION_HORIZON", ["14"])[0])
        effective_days = min(horizon, max_days) if max_days else horizon

        # Parse shifts
        shift_specs: dict[str, int] = {}
        for row in sections.get("SECTION_SHIFTS", []):
            parts = [p.strip() for p in row.split(",")]
            s_id = parts[0]
            length_min = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 480
            shift_specs[s_id] = length_min

        # Production Unit
        unit = ProductionUnit(id="unit_ward", name="Hospital Inpatient Ward", required_skills=["nursing"])

        # Concrete shifts per day
        shifts: list[Shift] = []
        for d in range(effective_days):
            for s_id, length_min in shift_specs.items():
                shifts.append(
                    Shift(
                        id=f"d{d}_{s_id}",
                        name=f"Day {d + 1} Shift {s_id}",
                        start_time="07:00",
                        end_time="15:00",
                        duration_hours=round(length_min / 60.0, 2),
                    )
                )

        # Days off
        days_off_map: dict[str, set[int]] = {}
        for row in sections.get("SECTION_DAYS_OFF", []):
            parts = [p.strip() for p in row.split(",") if p.strip()]
            if parts:
                staff_id = parts[0]
                days = set()
                for d_str in parts[1:]:
                    if d_str.isdigit():
                        days.add(int(d_str))
                days_off_map[staff_id] = days

        # Parse staff
        employees: list[Employee] = []
        for row in sections.get("SECTION_STAFF", []):
            parts = [p.strip() for p in row.split(",")]
            emp_id = parts[0]
            max_shifts_str = parts[1] if len(parts) > 1 else ""
            max_minutes = float(parts[2]) if len(parts) > 2 and parts[2].isdigit() else (effective_days * 8.0 * 60.0)

            # Check if any shift type has max=0 (e.g. L=0)
            forbidden_shifts = set()
            for token in max_shifts_str.split("|"):
                if "=" in token:
                    s_name, s_max = token.split("=")
                    if s_max.isdigit() and int(s_max) == 0:
                        forbidden_shifts.add(s_name)

            available: list[str] = []
            for d in range(effective_days):
                if d not in days_off_map.get(emp_id, set()):
                    for s_id in shift_specs:
                        if s_id not in forbidden_shifts:
                            available.append(f"d{d}_{s_id}")

            employees.append(
                Employee(
                    id=f"nurse_{emp_id}",
                    name=f"Nurse {emp_id}",
                    skills=["nursing"],
                    available_shifts=available,
                    max_hours=round(max_minutes / 60.0, 2),
                )
            )

        # Parse demands
        demands: list[Demand] = []
        for row in sections.get("SECTION_COVER", []):
            parts = [p.strip() for p in row.split(",")]
            if len(parts) >= 3 and parts[0].isdigit() and parts[2].isdigit():
                d_day = int(parts[0])
                s_id = parts[1]
                req_headcount = int(parts[2])
                if d_day < effective_days and req_headcount > 0:
                    demands.append(
                        Demand(
                            unit_id="unit_ward",
                            shift_id=f"d{d_day}_{s_id}",
                            required_headcount=req_headcount,
                        )
                    )

        scenario = Scenario(
            id=f"nr_{instance_id}",
            name=f"Nurse Rostering {file_path.stem} ({effective_days} days)",
            employees=employees,
            units=[unit],
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
            unit_count=1,
            shift_count=len(shifts),
            demand_count=len(demands),
            horizon_days=effective_days,
            compatibility_status=CompatibilityStatus.PARTIALLY_COMPATIBLE,
            supported_constraints=[
                "Staffing headcount demand", "Max hours limit",
                "Mandatory days off", "Single shift assignment per day"
            ],
            unsupported_constraints=[
                "Consecutive shift limits", "Min hours limit",
                "Weekend limits", "Shift transition rules"
            ],
            notes="Mapped onto Ordivanta single-ward staffing formulation."
        )

        return scenario, summary
