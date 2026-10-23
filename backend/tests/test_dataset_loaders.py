import pytest
from fastapi import HTTPException
from app.datasets import (
    dataset_registry,
    DatasetType,
    CompatibilityStatus,
    SyntheticManufacturingLoader,
    ShiftSchedulingLoader,
    PTSPLoader,
    NurseRosteringLoader,
)
from app.validation.input_validator import validate_scenario
from app.api.routes.datasets import (
    list_datasets,
    get_dataset,
    list_dataset_instances,
    get_instance_details,
)


def test_synthetic_loader():
    loader = SyntheticManufacturingLoader()
    meta = loader.get_metadata()
    assert meta.dataset_id == DatasetType.SYNTHETIC_MANUFACTURING.value
    assert meta.total_instances >= 3
    assert "employee.skills" in meta.fields_available

    instances = loader.list_instances()
    assert len(instances) >= 3

    scenario, summary = loader.load_instance("mfg_standard_sample")
    assert summary.compatibility_status == CompatibilityStatus.COMPATIBLE
    assert len(scenario.employees) == 10
    assert len(scenario.units) == 3
    assert len(scenario.shifts) == 3
    assert len(scenario.demands) == 9

    # Check scenario validity
    val_res = validate_scenario(scenario)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0


def test_shift_scheduling_loader():
    loader = ShiftSchedulingLoader()
    meta = loader.get_metadata()
    assert meta.dataset_id == DatasetType.SHIFT_SCHEDULING.value
    assert meta.total_instances == 225
    assert len(meta.unsupported_constraints) > 0

    instances = loader.list_instances()
    assert len(instances) == 225

    # Load first instance
    first = instances[0]
    scenario, summary = loader.load_instance(first.instance_id)
    assert summary.compatibility_status == CompatibilityStatus.PARTIALLY_COMPATIBLE
    assert len(scenario.employees) > 0
    assert len(scenario.units) > 0
    assert len(scenario.shifts) > 0
    assert len(scenario.demands) > 0

    # Ensure unsupported constraints are documented
    assert any(
        "Break" in c or "break" in c.lower()
        for c in summary.unsupported_constraints
    )

    # Validate scenario structure
    val_res = validate_scenario(scenario)
    assert val_res.is_valid is True


def test_ptsp_loader():
    loader = PTSPLoader()
    meta = loader.get_metadata()
    assert meta.dataset_id == DatasetType.PTSP.value
    assert meta.total_instances == 137

    instances = loader.list_instances()
    assert len(instances) == 137

    # Load first instance
    first = instances[0]
    scenario, summary = loader.load_instance(first.instance_id)
    assert summary.compatibility_status == CompatibilityStatus.PARTIALLY_COMPATIBLE
    assert len(scenario.employees) > 0
    assert len(scenario.units) == 1
    assert len(scenario.shifts) > 0
    assert len(scenario.demands) > 0

    # Continuous task interval overlap is flagged as unsupported
    assert any(
        "interval" in c.lower() or "overlap" in c.lower()
        for c in summary.unsupported_constraints
    )

    # Validate scenario structure
    val_res = validate_scenario(scenario)
    assert val_res.is_valid is True


def test_nurse_rostering_loader():
    loader = NurseRosteringLoader()
    meta = loader.get_metadata()
    assert meta.dataset_id == DatasetType.NURSE_ROSTERING.value
    assert meta.total_instances == 24

    instances = loader.list_instances()
    assert len(instances) == 24

    first = instances[0]
    scenario, summary = loader.load_instance(first.instance_id)
    assert summary.compatibility_status == CompatibilityStatus.PARTIALLY_COMPATIBLE
    assert len(scenario.employees) > 0
    assert len(scenario.shifts) > 0
    assert len(scenario.demands) > 0

    # Consecutive shift limits flagged as unsupported
    assert any(
        "consecutive" in c.lower() for c in summary.unsupported_constraints
    )

    # Validate scenario structure
    val_res = validate_scenario(scenario)
    assert val_res.is_valid is True


def test_registry_lookup_and_errors():
    datasets = dataset_registry.list_datasets()
    assert len(datasets) == 4

    # Unknown dataset
    with pytest.raises(KeyError):
        dataset_registry.get_loader("non_existent_dataset")

    # Unknown instance
    with pytest.raises(FileNotFoundError):
        dataset_registry.load_scenario(
            "nurse_rostering", "non_existent_file.txt"
        )


def test_dataset_api_handlers():
    # 1. List all datasets
    datasets = list_datasets()
    assert len(datasets) == 4
    ids = [d.dataset_id for d in datasets]
    assert "synthetic_manufacturing" in ids
    assert "shift_scheduling" in ids
    assert "ptsp" in ids
    assert "nurse_rostering" in ids

    # 2. Get specific dataset metadata
    meta = get_dataset("shift_scheduling")
    assert meta.dataset_id == "shift_scheduling"
    assert meta.total_instances == 225
    assert len(meta.mapped_constraints) > 0

    # 3. List instances
    instances = list_dataset_instances("nurse_rostering")
    assert len(instances) == 24
    assert instances[0].dataset_id == "nurse_rostering"

    # 4. Get instance details
    detail = get_instance_details("synthetic_manufacturing", "mfg_standard_sample")
    assert detail.instance_id == "mfg_standard_sample"
    assert detail.employee_count == 10

    # 5. Negative tests
    with pytest.raises(HTTPException) as exc_info:
        get_dataset("unknown_dataset_id")
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info:
        list_dataset_instances("unknown_dataset_id")
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info:
        get_instance_details("shift_scheduling", "non_existent_file.txt")
    assert exc_info.value.status_code == 404
