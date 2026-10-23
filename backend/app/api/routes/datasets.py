from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.persistence.database import get_session
from app.persistence import repository
from app.services.scenario_service import domain_to_response
from app.datasets.registry import dataset_registry
from app.schemas.dataset import (
    DatasetMetadataResponse,
    InstanceSummaryResponse,
    LoadInstanceResponse,
)

router = APIRouter()


def _to_instance_response(s) -> InstanceSummaryResponse:
    return InstanceSummaryResponse(
        instance_id=s.instance_id,
        dataset_id=s.dataset_id,
        name=s.name,
        filename=s.filename,
        employee_count=s.employee_count,
        unit_count=s.unit_count,
        shift_count=s.shift_count,
        demand_count=s.demand_count,
        horizon_days=s.horizon_days,
        compatibility_status=(
            s.compatibility_status.value
            if hasattr(s.compatibility_status, "value")
            else str(s.compatibility_status)
        ),
        supported_constraints=s.supported_constraints,
        unsupported_constraints=s.unsupported_constraints,
        notes=s.notes,
    )


def _to_dataset_response(m) -> DatasetMetadataResponse:
    return DatasetMetadataResponse(
        dataset_id=m.dataset_id,
        name=m.name,
        category=m.category,
        description=m.description,
        source_folder=m.source_folder,
        file_format=m.file_format,
        total_instances=m.total_instances,
        compatible_instances=m.compatible_instances,
        partially_compatible_instances=m.partially_compatible_instances,
        unsupported_instances=m.unsupported_instances,
        fields_available=m.fields_available,
        mapped_constraints=m.mapped_constraints,
        unsupported_constraints=m.unsupported_constraints,
        transformation_notes=m.transformation_notes,
    )


@router.get("/datasets", response_model=List[DatasetMetadataResponse])
def list_datasets():
    """List metadata and compatibility specifications for all registered datasets."""
    datasets = dataset_registry.list_datasets()
    return [_to_dataset_response(m) for m in datasets]


@router.get("/datasets/{dataset_id}", response_model=DatasetMetadataResponse)
def get_dataset(dataset_id: str):
    """Get metadata and compatibility documentation for a specific dataset."""
    m = dataset_registry.get_dataset_metadata(dataset_id)
    if not m:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )
    return _to_dataset_response(m)


@router.get(
    "/datasets/{dataset_id}/instances",
    response_model=List[InstanceSummaryResponse],
)
def list_dataset_instances(dataset_id: str):
    """List all instances available in a dataset with their size and compatibility."""
    try:
        instances = dataset_registry.list_instances(dataset_id)
        return [_to_instance_response(s) for s in instances]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list instances for '{dataset_id}': {str(e)}",
        )


@router.get(
    "/datasets/{dataset_id}/instances/{instance_id}",
    response_model=InstanceSummaryResponse,
)
def get_instance_details(dataset_id: str, instance_id: str):
    """Get detailed summary and constraint mapping for an instance."""
    summary = dataset_registry.get_instance_summary(dataset_id, instance_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instance '{instance_id}' not found in dataset '{dataset_id}'.",
        )
    return _to_instance_response(summary)


@router.post(
    "/datasets/{dataset_id}/load/{instance_id}",
    response_model=LoadInstanceResponse,
)
async def load_and_import_instance(
    dataset_id: str,
    instance_id: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Load a benchmark or synthetic instance, transform it into an Ordivanta domain Scenario,
    persist it to the database so it can be solved with MILP or Greedy, and return it.
    """
    try:
        scenario, summary = dataset_registry.load_scenario(
            dataset_id, instance_id
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse instance '{instance_id}': {str(e)}",
        )

    # Persist the transformed scenario into SQLite
    await repository.save_scenario(session, scenario)

    return LoadInstanceResponse(
        scenario=domain_to_response(scenario),
        instance_summary=_to_instance_response(summary),
        compatibility_status=(
            summary.compatibility_status.value
            if hasattr(summary.compatibility_status, "value")
            else str(summary.compatibility_status)
        ),
        notes=summary.notes,
    )
