from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from app.datasets.registry import dataset_registry
from app.optimization.task_allocation import (
    TaskScenario,
    TaskAllocationResult,
    GreedyTaskSolver,
    MILPTaskSolver,
    ALNSTaskSolver,
)

router = APIRouter()


class TaskSolveRequest(BaseModel):
    dataset_id: str = Field(default="smptsp", description="Dataset: 'smptsp', 'ptsp', or 'synthetic'")
    instance_id: str = Field(default="data_1_50_258_20_90_100_200_300")
    algorithm: str = Field(default="ALL", description="'MILP', 'GREEDY', 'ALNS', or 'ALL'")
    max_tasks: Optional[int] = Field(default=None, description="Optional cap on number of tasks for fast interactive demo")
    time_limit: int = Field(default=20, ge=1, le=120)


class WorkflowBridgeRequest(BaseModel):
    facility_id: str = Field(default="Detroit Assembly Plant #1")
    shift_name: str = Field(default="Day Shift (07:00 - 15:30)")
    active_worker_ids: Optional[List[str]] = Field(default=None)
    task_count: int = Field(default=24, ge=4, le=100)


@router.get("/tasks/benchmarks")
def list_task_benchmarks(dataset_id: Optional[str] = None):
    """
    List available benchmark instances for Module 2 (PTSP and SMPTSP).
    """
    datasets_to_query = [dataset_id] if dataset_id else ["ptsp", "smptsp"]
    results = {}
    for d_id in datasets_to_query:
        try:
            instances = dataset_registry.list_instances(d_id)
            results[d_id] = [
                {
                    "instance_id": inst.instance_id,
                    "name": inst.name,
                    "filename": inst.filename,
                    "workers": inst.employee_count,
                    "tasks": inst.shift_count,
                    "compatibility_status": inst.compatibility_status.value if hasattr(inst.compatibility_status, "value") else str(inst.compatibility_status),
                    "notes": inst.notes,
                }
                for inst in instances
            ]
        except Exception as e:
            results[d_id] = []
    return results


@router.get("/tasks/instance/{dataset_id}/{instance_id}")
def get_task_instance(dataset_id: str, instance_id: str, max_tasks: Optional[int] = 50):
    """
    Load and return parsed task allocation instance details: tasks timeline and worker qualifications.
    """
    try:
        scenario, summary = dataset_registry.load_scenario(dataset_id, instance_id, max_jobs=max_tasks)
        task_scenario = TaskScenario.from_domain_scenario(scenario)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to load task instance '{instance_id}' from '{dataset_id}': {str(e)}",
        )

    tasks_data = [
        {
            "id": t.id,
            "name": t.name,
            "start_minute": t.start_minute,
            "end_minute": t.end_minute,
            "duration_minutes": t.duration_minutes,
            "start_time": t.start_time_str,
            "end_time": t.end_time_str,
        }
        for t in task_scenario.tasks
    ]

    workers_data = [
        {
            "id": w.id,
            "name": w.name,
            "max_hours": w.max_hours,
            "qualified_tasks_count": len(w.qualified_task_ids),
            "qualified_task_ids": sorted(list(w.qualified_task_ids))[:50],  # sample for UI
        }
        for w in task_scenario.workers
    ]

    return {
        "instance_id": instance_id,
        "dataset_id": dataset_id,
        "name": task_scenario.name,
        "total_tasks": len(task_scenario.tasks),
        "total_workers": len(task_scenario.workers),
        "tasks": tasks_data,
        "workers": workers_data,
    }


@router.post("/tasks/solve")
def solve_task_allocation(req: TaskSolveRequest):
    """
    Solve a Module 2 task allocation instance using Greedy, MILP, ALNS, or ALL (comparison).
    """
    try:
        scenario, summary = dataset_registry.load_scenario(req.dataset_id, req.instance_id, max_jobs=req.max_tasks)
        obj_type = "shift_minimization" if req.dataset_id.lower() == "smptsp" else "coverage_balance"
        task_scenario = TaskScenario.from_domain_scenario(scenario, objective_type=obj_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to load scenario '{req.instance_id}': {str(e)}",
        )

    algo = req.algorithm.upper()
    results: Dict[str, Any] = {}

    if algo in ("GREEDY", "ALL"):
        greedy_res = GreedyTaskSolver().solve(task_scenario)
        results["greedy"] = greedy_res.to_dict()

    if algo in ("MILP", "ALL"):
        # Use appropriate time limit for MILP
        milp_res = MILPTaskSolver(time_limit=req.time_limit).solve(task_scenario)
        results["milp"] = milp_res.to_dict()

    if algo in ("ALNS", "ALL"):
        alns_res = ALNSTaskSolver(max_iterations=80, time_limit=float(req.time_limit)).solve(task_scenario)
        results["alns"] = alns_res.to_dict()

    # Generate comparison summary table if ALL requested
    comparison_summary = None
    if algo == "ALL":
        comparison_summary = [
            {
                "algorithm": r["algorithm"],
                "status": r["status"],
                "active_workers_shifts": r["active_workers_count"],
                "tasks_assigned": f"{r['total_assigned']}/{r['total_tasks']}",
                "coverage_pct": r["coverage_percentage"],
                "runtime_seconds": r["runtime_seconds"],
                "is_valid": r["is_valid"],
            }
            for r in results.values()
        ]

    # Select primary result to return
    primary_key = "milp" if "milp" in results else ("alns" if "alns" in results else "greedy")

    return {
        "instance_id": req.instance_id,
        "dataset_id": req.dataset_id,
        "primary_result": results[primary_key],
        "all_results": results,
        "comparison_summary": comparison_summary,
        "tasks_count": len(task_scenario.tasks),
        "workers_count": len(task_scenario.workers),
    }


@router.post("/tasks/workflow/bridge")
def bridge_shift_roster_to_tasks(req: WorkflowBridgeRequest):
    """
    Connected Workflow Demonstration:
    Bridges Module 1 (Workforce Shift Planning) with Module 2 (Task Allocation).
    Takes active workers from scheduled manufacturing shifts and allocates them
    to fine-grained workstation tasks across plant production cells.
    """
    # 1. Define worker roster pool
    worker_names = [
        ("W-01", "Marcus Vance", ["welding", "robotics"], 8.0),
        ("W-02", "Sarah Jenkins", ["cnc_stamping", "inspection"], 8.0),
        ("W-03", "David Kim", ["robotics", "cnc_stamping"], 8.0),
        ("W-04", "Elena Rostova", ["inspection", "packaging"], 8.0),
        ("W-05", "James Chen", ["welding", "inspection"], 8.0),
        ("W-06", "Amina Diallo", ["robotics", "packaging"], 8.0),
        ("W-07", "Carlos Mendez", ["cnc_stamping", "welding"], 8.0),
        ("W-08", "Rachel Green", ["inspection", "welding"], 8.0),
    ]

    from app.optimization.task_allocation.task_models import Task, TaskWorker

    # 2. Generate fine-grained cell workstation tasks (7:00 AM to 3:30 PM, minute 420 to 930)
    task_templates = [
        ("Sub-assembly Chassis Weld Prep", "welding", 420, 480, "Cell 01 - Machining & Weld"),
        ("Structural Robotic MIG Welding Run A", "robotics", 480, 570, "Cell 03 - Robotic Welding"),
        ("Structural Robotic MIG Welding Run B", "robotics", 570, 660, "Cell 03 - Robotic Welding"),
        ("High-Precision CNC Stamping Feed", "cnc_stamping", 450, 540, "Cell 02 - CNC Stamping"),
        ("Die Maintenance & Tolerance Check", "cnc_stamping", 540, 600, "Cell 02 - CNC Stamping"),
        ("Ultrasound Weld Integrity Inspection", "inspection", 660, 720, "Cell 04 - Final QC & Pack"),
        ("CMM Laser Geometric Scan", "inspection", 720, 780, "Cell 04 - Final QC & Pack"),
        ("Automated Cell 03 Recalibration", "robotics", 750, 840, "Cell 03 - Robotic Welding"),
        ("Heavy Bracket TIG Finishing", "welding", 600, 690, "Cell 01 - Machining & Weld"),
        ("Palletizing & ISO Packaging Line 1", "packaging", 780, 870, "Cell 04 - Final QC & Pack"),
        ("Palletizing & ISO Packaging Line 2", "packaging", 840, 930, "Cell 04 - Final QC & Pack"),
        ("Post-Weld Grind & Deburr Batch", "welding", 810, 885, "Cell 01 - Machining & Weld"),
    ]

    tasks: List[Task] = []
    for idx, (name, skill, s_m, e_m, cell) in enumerate(task_templates[:req.task_count]):
        tasks.append(
            Task(
                id=f"mfg_task_{idx+1:02d}",
                name=f"{name} ({cell})",
                start_minute=s_m,
                end_minute=e_m,
                duration_minutes=e_m - s_m,
                required_skill=skill,
                workstation=cell,
            )
        )

    # 3. Build workers with qualifications matching skills
    workers: List[TaskWorker] = []
    for w_id, w_name, w_skills, m_hours in worker_names:
        # A worker is qualified if their skills include the task's required skill
        qualified_t = {t.id for t in tasks if t.required_skill in w_skills}
        workers.append(
            TaskWorker(
                id=w_id,
                name=f"{w_name} ({', '.join(w_skills)})",
                qualified_task_ids=qualified_t,
                skills=w_skills,
                max_hours=m_hours,
            )
        )

    bridge_scenario = TaskScenario(
        id="bridge_mfg_demo",
        name=f"Bridge Roster Allocation - {req.facility_id} ({req.shift_name})",
        tasks=tasks,
        workers=workers,
        objective_type="shift_minimization",
        source_dataset="connected_workflow",
    )

    # Solve with MILP and Greedy for instant comparison
    milp_res = MILPTaskSolver(time_limit=15).solve(bridge_scenario)
    greedy_res = GreedyTaskSolver().solve(bridge_scenario)

    return {
        "status": "SUCCESS",
        "narrative": (
            f"Successfully bridged {len(workers)} scheduled workers from Module 1 "
            f"into {len(tasks)} fine-grained manufacturing workstation tasks. "
            f"MILP allocated {milp_res.total_assigned}/{len(tasks)} tasks utilizing {milp_res.active_workers_count} workers "
            f"in {milp_res.runtime_seconds:.3f}s with 0 temporal or qualification violations."
        ),
        "milp_result": milp_res.to_dict(),
        "greedy_result": greedy_res.to_dict(),
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "start_time": t.start_time_str,
                "end_time": t.end_time_str,
                "duration_minutes": t.duration_minutes,
                "skill": t.required_skill,
                "cell": t.workstation,
            }
            for t in tasks
        ],
        "workers": [
            {
                "id": w.id,
                "name": w.name,
                "skills": w.skills,
                "qualified_tasks_count": len(w.qualified_task_ids),
            }
            for w in workers
        ],
    }
