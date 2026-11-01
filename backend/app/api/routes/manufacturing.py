"""
API Routes for Manufacturing Operations: Plant Policy, Lifecycle, and Replacement Candidates.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.persistence.database import get_session
from app.domain.plant_policy import PlantPolicy, PlantPolicyResponse
from app.domain.schedule_lifecycle import (
    ScheduleLifecycleStatus,
    ScheduleLifecycleResponse,
    StatusTransitionRequest,
    ScheduleVersionMeta,
    ScheduleAuditEntry,
)
from app.services.scenario_service import get_scenario_domain
from app.services import schedule_service
from app.services.replacement_service import find_replacement_candidates
from app.domain.enums import QualificationPolicy

router = APIRouter(prefix="/manufacturing", tags=["manufacturing"])

# In-memory store for MVP demonstration (fast & lightweight)
_DEFAULT_POLICY = PlantPolicy(
    policy_id="policy_detroit_auto_01",
    plant_id="plant_mfg_01",
    name="Detroit Plant Core Manufacturing Policy 2026",
    version=1,
    is_active=True,
)

_LIFECYCLE_STORE: dict[str, ScheduleVersionMeta] = {}


@router.get("/policy", response_model=PlantPolicyResponse)
async def get_current_plant_policy():
    """Retrieve active manufacturing plant policy."""
    p = _DEFAULT_POLICY
    return PlantPolicyResponse(
        policy_id=p.policy_id,
        plant_id=p.plant_id,
        name=p.name,
        version=p.version,
        is_active=p.is_active,
        working_hours=p.working_hours.__dict__,
        qualification=p.qualification.__dict__,
        labor_cost=p.labor_cost.__dict__,
        lifecycle=p.lifecycle.__dict__,
        created_at=p.created_at,
    )


@router.get("/schedules/{run_id}/lifecycle", response_model=ScheduleLifecycleResponse)
async def get_schedule_lifecycle(run_id: str):
    """Retrieve lifecycle status and approval history for a schedule run."""
    meta = _LIFECYCLE_STORE.get(run_id)
    if not meta:
        # Default initial status is DRAFT
        meta = ScheduleVersionMeta(
            run_id=run_id,
            scenario_id="scenario_sample",
            version=1,
            lifecycle_status=ScheduleLifecycleStatus.DRAFT,
        )
        _LIFECYCLE_STORE[run_id] = meta

    can_publish = (meta.lifecycle_status == ScheduleLifecycleStatus.APPROVED)

    return ScheduleLifecycleResponse(
        run_id=meta.run_id,
        version=meta.version,
        lifecycle_status=meta.lifecycle_status,
        approved_by=meta.approved_by,
        published_by=meta.published_by,
        can_publish=can_publish,
        audit_history=[e.__dict__ for e in meta.audit_history],
    )


@router.post("/schedules/{run_id}/transition", response_model=ScheduleLifecycleResponse)
async def transition_schedule_status(run_id: str, req: StatusTransitionRequest):
    """Transition schedule lifecycle state with supervisor audit logging."""
    meta = _LIFECYCLE_STORE.get(run_id)
    if not meta:
        meta = ScheduleVersionMeta(
            run_id=run_id,
            scenario_id="scenario_sample",
            version=1,
            lifecycle_status=ScheduleLifecycleStatus.DRAFT,
        )
        _LIFECYCLE_STORE[run_id] = meta

    # Lifecycle validation rules
    current = meta.lifecycle_status
    target = req.to_status

    if target == ScheduleLifecycleStatus.PUBLISHED and current != ScheduleLifecycleStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail="Schedule must be APPROVED by Operations Manager before it can be PUBLISHED to the shop floor.",
        )

    # Record audit log
    entry = ScheduleAuditEntry(
        entry_id=f"audit_{len(meta.audit_history)+1}",
        run_id=run_id,
        from_status=current,
        to_status=target,
        actor_id=req.actor_id,
        actor_role=req.actor_role,
        notes=req.notes,
    )
    meta.audit_history.append(entry)
    meta.lifecycle_status = target

    if target == ScheduleLifecycleStatus.APPROVED:
        meta.approved_by = req.actor_id
    elif target == ScheduleLifecycleStatus.PUBLISHED:
        meta.published_by = req.actor_id

    return ScheduleLifecycleResponse(
        run_id=meta.run_id,
        version=meta.version,
        lifecycle_status=meta.lifecycle_status,
        approved_by=meta.approved_by,
        published_by=meta.published_by,
        can_publish=(meta.lifecycle_status == ScheduleLifecycleStatus.APPROVED),
        audit_history=[e.__dict__ for e in meta.audit_history],
    )


@router.get("/shortages/replacements")
async def get_shortage_replacement_candidates(
    scenario_id: str,
    unit_id: str,
    shift_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Retrieve ranked replacement candidates for an understaffed shift position."""
    scenario = await get_scenario_domain(session, scenario_id)
    candidates = find_replacement_candidates(
        scenario=scenario,
        target_unit_id=unit_id,
        target_shift_id=shift_id,
        currently_assigned_hours={},
        assigned_shifts_by_emp={},
        qualification_policy=QualificationPolicy.LEVEL_AND_CERTIFICATION,
        min_rest_hours=11.0,
    )
    return [c.__dict__ for c in candidates]
