from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.domain.models import Scenario
from .base import (
    BaseDatasetLoader,
    CompatibilityStatus,
    DatasetMetadata,
    DatasetType,
    InstanceSummary,
)
from .synthetic_loader import SyntheticManufacturingLoader
from .shift_scheduling_loader import ShiftSchedulingLoader
from .ptsp_loader import PTSPLoader
from .nurse_rostering_loader import NurseRosteringLoader


class DatasetRegistry:
    """
    Central catalog and registry for all workforce scheduling benchmark and synthetic datasets.
    Provides uniform interfaces for metadata discovery, instance listing, and transformation.
    """

    def __init__(self):
        self._loaders: Dict[str, BaseDatasetLoader] = {
            DatasetType.SYNTHETIC_MANUFACTURING.value: SyntheticManufacturingLoader(),
            DatasetType.SHIFT_SCHEDULING.value: ShiftSchedulingLoader(),
            DatasetType.PTSP.value: PTSPLoader(),
            DatasetType.NURSE_ROSTERING.value: NurseRosteringLoader(),
        }

    def register_loader(self, dataset_id: str, loader: BaseDatasetLoader) -> None:
        self._loaders[dataset_id] = loader

    def get_loader(self, dataset_id: str) -> BaseDatasetLoader:
        loader = self._loaders.get(dataset_id)
        if not loader:
            raise KeyError(
                f"Dataset '{dataset_id}' not found. Available datasets: {list(self._loaders.keys())}"
            )
        return loader

    def list_datasets(self) -> List[DatasetMetadata]:
        """Return metadata for all registered datasets."""
        return [loader.get_metadata() for loader in self._loaders.values()]

    def get_dataset_metadata(self, dataset_id: str) -> Optional[DatasetMetadata]:
        """Return metadata for a specific dataset."""
        loader = self._loaders.get(dataset_id)
        return loader.get_metadata() if loader else None

    def list_instances(self, dataset_id: str) -> List[InstanceSummary]:
        """List all instances for a given dataset."""
        loader = self.get_loader(dataset_id)
        return loader.list_instances()

    def get_instance_summary(
        self, dataset_id: str, instance_id: str
    ) -> Optional[InstanceSummary]:
        """Get summary for a specific instance."""
        instances = self.list_instances(dataset_id)
        for inst in instances:
            if inst.instance_id == instance_id:
                return inst
        return None

    def load_scenario(
        self, dataset_id: str, instance_id: str, **kwargs
    ) -> Tuple[Scenario, InstanceSummary]:
        """Load and transform a dataset instance into an Ordivanta domain Scenario."""
        loader = self.get_loader(dataset_id)
        return loader.load_instance(instance_id, **kwargs)


# Global singleton instance
dataset_registry = DatasetRegistry()
