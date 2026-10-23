from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from app.domain.models import Scenario


class DatasetType(str, Enum):
    SYNTHETIC_MANUFACTURING = "synthetic_manufacturing"
    SHIFT_SCHEDULING = "shift_scheduling"
    PTSP = "ptsp"
    NURSE_ROSTERING = "nurse_rostering"


class CompatibilityStatus(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    PARTIALLY_COMPATIBLE = "PARTIALLY_COMPATIBLE"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass
class InstanceSummary:
    instance_id: str
    dataset_id: str
    name: str
    filename: str
    employee_count: int
    unit_count: int
    shift_count: int
    demand_count: int
    horizon_days: int | None
    compatibility_status: CompatibilityStatus
    supported_constraints: list[str] = field(default_factory=list)
    unsupported_constraints: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class DatasetMetadata:
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
    fields_available: list[str]
    mapped_constraints: list[str]
    unsupported_constraints: list[str]
    transformation_notes: str


class BaseDatasetLoader(ABC):
    @abstractmethod
    def get_metadata(self) -> DatasetMetadata:
        """Return dataset level metadata and compatibility documentation."""
        pass

    @abstractmethod
    def list_instances(self) -> list[InstanceSummary]:
        """List all instances in this dataset with metadata."""
        pass

    @abstractmethod
    def load_instance(self, instance_id: str, **kwargs) -> tuple[Scenario, InstanceSummary]:
        """Load and transform an instance into an Ordivanta domain Scenario."""
        pass
