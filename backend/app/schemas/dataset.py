from pydantic import BaseModel
from typing import Optional, List
from .scenario import ScenarioResponse


class InstanceSummaryResponse(BaseModel):
    instance_id: str
    dataset_id: str
    name: str
    filename: str
    employee_count: int
    unit_count: int
    shift_count: int
    demand_count: int
    horizon_days: Optional[int] = None
    compatibility_status: str
    supported_constraints: List[str] = []
    unsupported_constraints: List[str] = []
    notes: str = ""


class DatasetMetadataResponse(BaseModel):
    dataset_id: str
    name: str
    category: str
    description: str
    source_folder: str
    file_format: str
    total_instances: int
    compatible_instances: int
    partially_compatible_instances: int
    unsupported_instances: int
    fields_available: List[str]
    mapped_constraints: List[str]
    unsupported_constraints: List[str]
    transformation_notes: str


class LoadInstanceResponse(BaseModel):
    scenario: ScenarioResponse
    instance_summary: InstanceSummaryResponse
    compatibility_status: str
    notes: str
