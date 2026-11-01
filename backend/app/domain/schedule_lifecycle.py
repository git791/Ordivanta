"""
Schedule Lifecycle Enums, State Transition Models, and Audit Logs.
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from pydantic import BaseModel


class ScheduleLifecycleStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"


@dataclass
class ScheduleAuditEntry:
    entry_id: str
    run_id: str
    from_status: ScheduleLifecycleStatus
    to_status: ScheduleLifecycleStatus
    actor_id: str
    actor_role: str
    notes: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ScheduleVersionMeta:
    run_id: str
    scenario_id: str
    version: int
    lifecycle_status: ScheduleLifecycleStatus = ScheduleLifecycleStatus.DRAFT
    created_by: str = "system"
    approved_by: str | None = None
    published_by: str | None = None
    audit_history: list[ScheduleAuditEntry] = field(default_factory=list)


# Pydantic Schemas
class StatusTransitionRequest(BaseModel):
    to_status: ScheduleLifecycleStatus
    actor_id: str
    actor_role: str = "Supervisor"
    notes: str = ""


class ScheduleLifecycleResponse(BaseModel):
    run_id: str
    version: int
    lifecycle_status: ScheduleLifecycleStatus
    approved_by: str | None = None
    published_by: str | None = None
    can_publish: bool
    audit_history: list[dict]
