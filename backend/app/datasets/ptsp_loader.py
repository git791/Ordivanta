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


class PTSPLoader(BaseDatasetLoader):
    """
    Loader for the Personnel Task Scheduling Problem (PTSP) Benchmark (ptask/ptsp).
    Format: Jobs with specific start/end execution minutes, worker multi-skilling
    qualification lists, and single-worker staffing requirements.
    """

    def __init__(self, data_dir: Path | None = None):
        self.dataset_id = DatasetType.PTSP.value
        if data_dir is not None:
            self.data_dir = data_dir
        else:
            root = Path(__file__).resolve().parents[3]
            self.data_dir = root / "data" / "ptask" / "ptsp"

    def get_metadata(self) -> DatasetMetadata:
        total = len(list(self.data_dir.glob("*.dat"))) if self.data_dir.exists() else 137
        return DatasetMetadata(
            dataset_id=self.dataset_id,
            name="Personnel Task Scheduling Problem (PTSP)",
            category="Supplementary Task Scheduling Benchmark",
            description=(
                "Personnel Task Scheduling Problem (PTSP) benchmark instances (Krishnamoorthy, Ernst, Baatar / Smet). "
                "Models individual task execution intervals on a continuous timeline, worker multi-skilling qualifications, "
                "and job assignment coverage."
            ),
            source_folder="data/ptask/ptsp/",
            file_format="PTSP datagen data specification (.dat)",
            total_instances=total,
            compatible_instances=total,
            partially_compatible_instances=total,
            unsupported_instances=0,
            fields_available=[
                "Type = 1 (problem type identifier)",
                "Jobs = N (total count of discrete tasks)",
                "Job intervals (start minute, end minute within 24-hour cycle)",
                "Qualifications = M (worker headcount / qualification profile count)",
                "Worker eligibility list (count and specific list of qualified job IDs per worker)"
            ],
            mapped_constraints=[
                "Task staffing coverage (headcount = 1 worker per job)",
                "Worker qualification compatibility (mapped via multi-skilling available_shifts)",
                "Task duration in hours (end_minute - start_minute) / 60.0",
                "Single worker assignment per task (sum_i x_{ijs} >= 1)",
                "Worker daily working-hours limit"
            ],
            unsupported_constraints=[
                "Continuous timeline pairwise task non-overlap: In PTSP, tasks have continuous start/end minutes. "
                "Ordivanta enforces that a worker works at most one unit per discrete shift slot, but does not "
                "automatically enforce continuous interval non-overlap between two distinct overlapping shifts."
            ],
            transformation_notes=(
                "Each job is mapped to an Ordivanta Shift with start_time, end_time, and duration_hours. "
                "A central task execution ProductionUnit ('unit_ptsp_ops') requires 1 worker per job. "
                "Worker eligibility lists are transformed into worker shift availability mappings. "
                "Continuous interval non-overlap across distinct jobs is flagged as an unsupported constraint."
            ),
        )

    def list_instances(self) -> list[InstanceSummary]:
        if not self.data_dir.exists():
            return []

        # Sort files by size
        files = sorted(self.data_dir.glob("*.dat"), key=lambda p: p.stat().st_size)
        summaries = []

        for p in files:
            instance_id = p.stem.lower()
            try:
                # Parse filename e.g. data_2_24_40_33.dat -> index 2, 24 workers, 40 jobs, 33% multiskill
                parts = p.stem.split("_")
                workers = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 24
                jobs = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 40
                multiskill = parts[4] if len(parts) > 4 else "33"

                summaries.append(
                    InstanceSummary(
                        instance_id=instance_id,
                        dataset_id=self.dataset_id,
                        name=f"PTSP {p.stem} ({workers} workers, {jobs} jobs, {multiskill}% skill)",
                        filename=p.name,
                        employee_count=workers,
                        unit_count=1,
                        shift_count=jobs,
                        demand_count=jobs,
                        horizon_days=1,
                        compatibility_status=CompatibilityStatus.PARTIALLY_COMPATIBLE,
                        supported_constraints=[
                            "Task coverage (1 worker/job)", "Worker qualification match",
                            "Daily working hours cap"
                        ],
                        unsupported_constraints=[
                            "Continuous pairwise task time overlap"
                        ],
                        notes=f"Personnel task scheduling with {multiskill}% multi-skilling level."
                    )
                )
            except Exception:
                continue

        return summaries

    def load_instance(self, instance_id: str, max_jobs: int | None = None, **kwargs) -> tuple[Scenario, InstanceSummary]:
        target_name = f"{instance_id}.dat"
        file_path = None
        for p in self.data_dir.glob("*.dat"):
            if p.stem.lower() == instance_id.lower() or p.name.lower() == target_name.lower():
                file_path = p
                break

        if not file_path or not file_path.exists():
            raise FileNotFoundError(f"Instance '{instance_id}' not found in {self.data_dir}")

        lines = [l.strip() for l in file_path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("#")]

        # Parse jobs count
        num_jobs = 0
        job_lines: list[tuple[int, int]] = []
        qual_lines: list[list[int]] = []
        mode = "header"

        for line in lines:
            if line.startswith("Jobs ="):
                num_jobs = int(line.split("=")[1].strip())
                mode = "jobs"
            elif line.startswith("Qualifications ="):
                mode = "qualifications"
            elif mode == "jobs":
                parts = line.split()
                if len(parts) >= 2:
                    start_m = int(parts[0])
                    end_m = int(parts[1])
                    job_lines.append((start_m, end_m))
            elif mode == "qualifications":
                # Line format: "10: 5 12 7 13..."
                if ":" in line:
                    _, job_part = line.split(":", 1)
                    q_jobs = [int(x) for x in job_part.split() if x.isdigit()]
                    qual_lines.append(q_jobs)
                else:
                    q_jobs = [int(x) for x in line.split() if x.isdigit()]
                    if qual_lines:
                        qual_lines[-1].extend(q_jobs)

        effective_jobs = len(job_lines)
        if max_jobs and max_jobs < effective_jobs:
            effective_jobs = max_jobs
            job_lines = job_lines[:effective_jobs]

        # Central Operations Unit
        unit = ProductionUnit(id="unit_ptsp_ops", name="Personnel Task Operations Area", required_skills=["task_skill"])

        # Shifts from jobs
        shifts: list[Shift] = []
        demands: list[Demand] = []

        for j_idx, (start_m, end_m) in enumerate(job_lines):
            duration_m = max(15, end_m - start_m)
            start_h = f"{start_m // 60:02d}:{start_m % 60:02d}"
            end_h = f"{end_m // 60:02d}:{end_m % 60:02d}"
            shift_id = f"job_{j_idx}"

            shifts.append(
                Shift(
                    id=shift_id,
                    name=f"Job {j_idx} ({start_h}–{end_h})",
                    start_time=start_h,
                    end_time=end_h,
                    duration_hours=round(duration_m / 60.0, 2),
                )
            )

            demands.append(
                Demand(
                    unit_id="unit_ptsp_ops",
                    shift_id=shift_id,
                    required_headcount=1,
                )
            )

        # Workers from qualifications
        employees: list[Employee] = []
        for w_idx, q_jobs in enumerate(qual_lines):
            available = [f"job_{j}" for j in q_jobs if j < effective_jobs]
            employees.append(
                Employee(
                    id=f"ptsp_worker_{w_idx}",
                    name=f"Worker {w_idx}",
                    skills=["task_skill"],
                    available_shifts=available,
                    max_hours=24.0,  # Single-day continuous shift limit
                )
            )

        scenario = Scenario(
            id=f"ptsp_{instance_id}",
            name=f"PTSP {file_path.stem} ({len(employees)} staff, {len(shifts)} jobs)",
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
            horizon_days=1,
            compatibility_status=CompatibilityStatus.PARTIALLY_COMPATIBLE,
            supported_constraints=[
                "Task coverage (1 worker/job)", "Worker qualification match",
                "Daily working hours cap"
            ],
            unsupported_constraints=[
                "Continuous pairwise task time overlap"
            ],
            notes="Personnel task scheduling with multi-skilling qualification matrix."
        )

        return scenario, summary
