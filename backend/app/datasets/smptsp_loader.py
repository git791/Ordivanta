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


class SMPTSPLoader(BaseDatasetLoader):
    """
    Loader for the Shift Minimisation Personnel Task Scheduling Problem (SMPTSP) Benchmark (Smet et al.).
    Public repository: psmet1/smptsp.
    Format: Jobs with specific start/end execution minutes, worker multi-skilling
    qualification lists, with objective of minimizing total shifts / distinct workers utilized.
    """

    def __init__(self, data_dir: Path | None = None):
        self.dataset_id = DatasetType.SMPTSP.value
        if data_dir is not None:
            self.data_dir = data_dir
        else:
            import os
            env_dir = os.environ.get("ORDIVANTA_DATA_DIR")
            if env_dir:
                candidate = Path(env_dir) / "smptsp" / "instances"
                if candidate.exists():
                    self.data_dir = candidate
                    return
            root = Path(__file__).resolve().parents[3]
            self.data_dir = root / "data" / "smptsp" / "instances"

    def get_metadata(self) -> DatasetMetadata:
        total = len(list(self.data_dir.glob("*.dat"))) if self.data_dir.exists() else 10
        return DatasetMetadata(
            dataset_id=self.dataset_id,
            name="Shift Minimisation Personnel Task Scheduling Problem (SMPTSP)",
            category="Module 2 Benchmark (Task Allocation & Shift Minimisation)",
            description=(
                "Shift Minimisation Personnel Task Scheduling Problem (SMPTSP) benchmark instances "
                "from Smet, Wauters, Mihaylov, Vanden Berghe (2014, 2016). Evaluates assigning qualified "
                "workers to non-overlapping fixed-time tasks while minimizing the total number of shifts / "
                "active personnel utilized across the operational day."
            ),
            source_folder="data/smptsp/instances/",
            file_format="SMPTSP/PTSP datagen specification (.dat)",
            total_instances=total,
            compatible_instances=total,
            partially_compatible_instances=total,
            unsupported_instances=0,
            fields_available=[
                "Type = 1 (problem type identifier)",
                "Jobs = N (total count of discrete tasks, up to 1,577 tasks)",
                "Job intervals (start minute, end minute within 1440-minute operational horizon)",
                "Qualifications = M (worker pool count, up to 153 workers)",
                "Worker eligibility list (count and specific list of qualified job IDs per worker)",
                "Tightness and multi-skilling levels (e.g., 20% to 30% multi-skilling, 90% tightness)"
            ],
            mapped_constraints=[
                "Task staffing coverage (headcount = 1 worker per job)",
                "Worker qualification compatibility (strict skill eligibility matching)",
                "Task duration in hours: (end_minute - start_minute) / 60.0",
                "Continuous timeline pairwise task non-overlap: If task i and task j overlap, worker w cannot do both",
                "Shift minimisation objective: Minimize active worker shifts (distinct workers assigned >= 1 task)",
                "Worker daily working-hours limit"
            ],
            unsupported_constraints=[
                "Arbitrary task preemption/splitting (tasks are continuous indivisible operations)",
                "Workstation travel matrix between distinct physical floor areas"
            ],
            transformation_notes=(
                "Each job is mapped to a discrete task interval with start/end time. "
                "Worker eligibility lists define strict skill qualification mapping. "
                "In Module 2, the dedicated task-allocation formulations (Greedy, MILP, ALNS) "
                "explicitly optimize shift minimization and task coverage."
            ),
        )

    def list_instances(self) -> list[InstanceSummary]:
        if not self.data_dir.exists():
            return []

        files = sorted(self.data_dir.glob("*.dat"), key=lambda p: p.stat().st_size)
        summaries = []

        for p in files:
            instance_id = p.stem.lower()
            try:
                # Parse filename e.g. data_1_50_258_20_90_100_200_300.dat -> index 1, 50 workers, 258 jobs
                parts = p.stem.split("_")
                workers = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 50
                jobs = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 258
                multiskill = parts[4] if len(parts) > 4 else "20"
                tightness = parts[5] if len(parts) > 5 else "90"

                summaries.append(
                    InstanceSummary(
                        instance_id=instance_id,
                        dataset_id=self.dataset_id,
                        name=f"SMPTSP {p.stem} ({workers} workers, {jobs} tasks, {multiskill}% skill)",
                        filename=p.name,
                        employee_count=workers,
                        unit_count=1,
                        shift_count=jobs,
                        demand_count=jobs,
                        horizon_days=1,
                        compatibility_status=CompatibilityStatus.COMPATIBLE,
                        supported_constraints=[
                            "Coverage: Exactly 1 worker per task",
                            "Worker Qualifications: Strict eligibility matching",
                            "Temporal Non-Overlap: [start, end) disjoint per worker",
                            "Shift Minimisation: Minimize active worker count / shifts",
                        ],
                        unsupported_constraints=[
                            "Task preemption / mid-operation splitting",
                            "Physical travel matrix",
                        ],
                        notes=f"SMPTSP benchmark instance with {workers} workers, {jobs} tasks, tightness={tightness}%, multiskilling={multiskill}%.",
                    )
                )
            except Exception as e:
                summaries.append(
                    InstanceSummary(
                        instance_id=instance_id,
                        dataset_id=self.dataset_id,
                        name=f"SMPTSP {p.stem}",
                        filename=p.name,
                        employee_count=50,
                        unit_count=1,
                        shift_count=200,
                        demand_count=200,
                        horizon_days=1,
                        compatibility_status=CompatibilityStatus.PARTIALLY_COMPATIBLE,
                        notes=f"Parse fallback: {e}",
                    )
                )

        return summaries

    def load_instance(self, instance_id: str, **kwargs) -> tuple[Scenario, InstanceSummary]:
        max_jobs = kwargs.get("max_jobs")
        file_path = None
        for ext in [".dat", ".DAT"]:
            p = self.data_dir / f"{instance_id}{ext}"
            if p.exists():
                file_path = p
                break

        if not file_path:
            # Fallback search by stem
            for p in self.data_dir.glob("*.dat"):
                if p.stem.lower() == instance_id.lower():
                    file_path = p
                    break

        if not file_path or not file_path.exists():
            raise FileNotFoundError(f"Instance '{instance_id}' not found in {self.data_dir}")

        lines = [l.strip() for l in file_path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("#")]

        job_lines: list[tuple[int, int]] = []
        qual_lines: list[list[int]] = []
        mode = "header"

        for line in lines:
            if line.startswith("Jobs ="):
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
                if ":" in line:
                    _, job_part = line.split(":", 1)
                    q_jobs = [int(x) for x in job_part.split() if x.isdigit()]
                    qual_lines.append(q_jobs)
                else:
                    q_jobs = [int(x) for x in line.split() if x.isdigit()]
                    if qual_lines:
                        qual_lines[-1].extend(q_jobs)

        original_job_count = len(job_lines)
        is_reduced = bool(max_jobs and max_jobs < original_job_count)
        effective_jobs = original_job_count
        if is_reduced:
            effective_jobs = max_jobs
            job_lines = job_lines[:effective_jobs]

        unit = ProductionUnit(id="unit_smptsp_ops", name="SMPTSP Workstation Tasks Area", required_skills=["task_skill"])

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
                    name=f"Task {j_idx} ({start_h}–{end_h})",
                    start_time=start_h,
                    end_time=end_h,
                    duration_hours=round(duration_m / 60.0, 2),
                )
            )

            demands.append(
                Demand(
                    unit_id="unit_smptsp_ops",
                    shift_id=shift_id,
                    required_headcount=1,
                )
            )

        employees: list[Employee] = []
        for w_idx, q_jobs in enumerate(qual_lines):
            available = [f"job_{j}" for j in q_jobs if j < effective_jobs]
            employees.append(
                Employee(
                    id=f"smptsp_worker_{w_idx}",
                    name=f"Worker {w_idx}",
                    skills=["task_skill"],
                    available_shifts=available,
                    max_hours=24.0,
                )
            )

        subset_label = f" (Reduced Subset: {effective_jobs} tasks)" if is_reduced else ""
        scenario = Scenario(
            id=f"smptsp_{instance_id}",
            name=f"SMPTSP {file_path.stem} ({len(employees)} workers, {len(shifts)} tasks){subset_label}",
            employees=employees,
            units=[unit],
            shifts=shifts,
            demands=demands,
            created_at=datetime.utcnow(),
        )

        subset_note = (
            f" [Reduced subset of {effective_jobs}/{original_job_count} tasks; worker eligibility and interval timestamps preserved.]"
            if is_reduced else ""
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
            compatibility_status=CompatibilityStatus.COMPATIBLE,
            supported_constraints=[
                "Coverage: Exactly 1 worker per task",
                "Worker Qualifications: Strict eligibility matching",
                "Temporal Non-Overlap: [start, end) disjoint per worker",
                "Shift Minimisation: Minimize active workers / shifts",
            ],
            unsupported_constraints=[
                "Task preemption / splitting",
                "Physical travel matrix",
            ],
            notes=f"Loaded {len(shifts)} tasks and {len(employees)} workers from {file_path.name}.{subset_note}",
        )

        return scenario, summary
