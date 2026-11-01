"""
Plant Policy Domain Models and Repository Entities.
"""
from dataclasses import dataclass, field
from datetime import datetime
from pydantic import BaseModel
from app.domain.enums import QualificationPolicy


@dataclass
class WorkingHoursPolicy:
    regular_hours_limit: float = 40.0
    max_overtime_hours: float = 10.0
    require_overtime_consent: bool = True
    min_rest_hours_between_shifts: float = 11.0
    max_consecutive_days: int = 6


@dataclass
class QualificationPolicyConfig:
    default_policy: QualificationPolicy = QualificationPolicy.LEVEL_AND_CERTIFICATION
    enforce_proficiency_levels: bool = True
    enforce_certifications: bool = True


@dataclass
class LaborCostPolicy:
    currency: str = "USD"
    default_base_rate: float = 28.50
    overtime_premium_multiplier: float = 0.50  # 1.5x time pay = 0.5x additive premium


@dataclass
class LifecyclePolicy:
    require_manager_approval_to_publish: bool = True
    freeze_horizon_hours: float = 24.0


@dataclass
class PlantPolicy:
    policy_id: str
    plant_id: str
    name: str
    version: int = 1
    is_active: bool = True
    working_hours: WorkingHoursPolicy = field(default_factory=WorkingHoursPolicy)
    qualification: QualificationPolicyConfig = field(default_factory=QualificationPolicyConfig)
    labor_cost: LaborCostPolicy = field(default_factory=LaborCostPolicy)
    lifecycle: LifecyclePolicy = field(default_factory=LifecyclePolicy)
    created_at: datetime = field(default_factory=datetime.utcnow)


# Pydantic Schemas for API Exposure
class WorkingHoursPolicySchema(BaseModel):
    regular_hours_limit: float = 40.0
    max_overtime_hours: float = 10.0
    require_overtime_consent: bool = True
    min_rest_hours_between_shifts: float = 11.0
    max_consecutive_days: int = 6


class QualificationPolicyConfigSchema(BaseModel):
    default_policy: QualificationPolicy = QualificationPolicy.LEVEL_AND_CERTIFICATION
    enforce_proficiency_levels: bool = True
    enforce_certifications: bool = True


class LaborCostPolicySchema(BaseModel):
    currency: str = "USD"
    default_base_rate: float = 28.50
    overtime_premium_multiplier: float = 0.50


class LifecyclePolicySchema(BaseModel):
    require_manager_approval_to_publish: bool = True
    freeze_horizon_hours: float = 24.0


class PlantPolicyResponse(BaseModel):
    policy_id: str
    plant_id: str
    name: str
    version: int
    is_active: bool
    working_hours: WorkingHoursPolicySchema
    qualification: QualificationPolicyConfigSchema
    labor_cost: LaborCostPolicySchema
    lifecycle: LifecyclePolicySchema
    created_at: datetime
