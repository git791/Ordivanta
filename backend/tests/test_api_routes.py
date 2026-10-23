import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_route(async_client: AsyncClient):
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "solver_available" in data
    assert "solver_name" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_workforce_routes(async_client: AsyncClient):
    # 1. Employees
    emp_payload = {
        "id": "EMP_TEST_1",
        "name": "Test Worker",
        "skills": ["assembly"],
        "available_shifts": ["S1"],
        "max_hours": 40.0,
    }
    res = await async_client.post("/api/employees", json=emp_payload)
    assert res.status_code == 201
    created_emp = res.json()
    assert created_emp["id"] == "EMP_TEST_1"

    res_list = await async_client.get("/api/employees")
    assert res_list.status_code == 200
    assert any(e["id"] == "EMP_TEST_1" for e in res_list.json())

    # 2. Units
    unit_payload = {
        "id": "UNIT_TEST_1",
        "name": "Test Unit",
        "required_skills": ["assembly"],
    }
    res = await async_client.post("/api/units", json=unit_payload)
    assert res.status_code == 201
    created_unit = res.json()
    assert created_unit["id"] == "UNIT_TEST_1"

    res_units = await async_client.get("/api/units")
    assert res_units.status_code == 200
    assert any(u["id"] == "UNIT_TEST_1" for u in res_units.json())

    # 3. Shifts
    shift_payload = {
        "id": "SHIFT_TEST_1",
        "name": "Day Shift",
        "start_time": "08:00",
        "end_time": "16:00",
        "duration_hours": 8.0,
    }
    res = await async_client.post("/api/shifts", json=shift_payload)
    assert res.status_code == 201
    created_shift = res.json()
    assert created_shift["id"] == "SHIFT_TEST_1"

    res_shifts = await async_client.get("/api/shifts")
    assert res_shifts.status_code == 200
    assert any(s["id"] == "SHIFT_TEST_1" for s in res_shifts.json())


@pytest.mark.asyncio
async def test_scenarios_lifecycle(async_client: AsyncClient):
    # 1. Load sample scenario
    res_sample = await async_client.post("/api/scenarios/sample")
    assert res_sample.status_code == 200
    sample_data = res_sample.json()
    scenario_id = sample_data["id"]
    assert scenario_id == "scenario_sample"
    assert len(sample_data["employees"]) == 10

    # 2. List scenarios
    res_list = await async_client.get("/api/scenarios")
    assert res_list.status_code == 200
    summaries = res_list.json()
    assert any(s["id"] == scenario_id for s in summaries)

    # 3. Get scenario by ID
    res_get = await async_client.get(f"/api/scenarios/{scenario_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == scenario_id

    # 4. Validate scenario
    res_val = await async_client.post(f"/api/scenarios/{scenario_id}/validate")
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["is_valid"] is True
    assert len(val_data["errors"]) == 0

    # 5. Non-existent scenario returns 404 with structured error
    res_404 = await async_client.get("/api/scenarios/non_existent_id")
    assert res_404.status_code == 404
    err_body = res_404.json()
    assert "errors" in err_body
    assert err_body["errors"][0]["code"] == "SCENARIO_NOT_FOUND"

    # 6. Delete scenario
    res_del = await async_client.delete(f"/api/scenarios/{scenario_id}")
    assert res_del.status_code == 204

    # Verify deletion
    res_after_del = await async_client.get(f"/api/scenarios/{scenario_id}")
    assert res_after_del.status_code == 404


@pytest.mark.asyncio
async def test_schedules_solve_and_export(async_client: AsyncClient):
    # 1. Load a scenario first
    res_sample = await async_client.post("/api/scenarios/sample")
    assert res_sample.status_code == 200
    scenario_id = res_sample.json()["id"]

    # 2. Solve with MILP
    solve_req = {
        "scenario_id": scenario_id,
        "algorithm": "milp",
        "objective": {
            "primary": "feasibility",
            "include_assignment_cost": False,
            "fairness_weight": 0.0,
        },
        "time_limit_seconds": 10,
    }
    res_solve = await async_client.post("/api/schedules/solve", json=solve_req)
    assert res_solve.status_code == 200
    solve_data = res_solve.json()
    run_id = solve_data["run_id"]
    assert solve_data["algorithm"] == "milp"
    assert solve_data["status"] == "OPTIMAL"
    assert solve_data["metrics"]["total_required_positions"] == 27
    assert len(solve_data["assignments"]) == 27

    # 3. List runs
    res_runs = await async_client.get("/api/schedules")
    assert res_runs.status_code == 200
    runs = res_runs.json()
    assert any(r["run_id"] == run_id for r in runs)

    # 4. Get specific run
    res_run = await async_client.get(f"/api/schedules/{run_id}")
    assert res_run.status_code == 200
    assert res_run.json()["run_id"] == run_id

    # 5. Get run metrics
    res_metrics = await async_client.get(f"/api/schedules/{run_id}/metrics")
    assert res_metrics.status_code == 200
    metrics = res_metrics.json()
    assert "coverage_rate" in metrics
    assert "hard_constraint_violations" in metrics

    # 6. Export CSV
    res_export = await async_client.get(f"/api/schedules/{run_id}/export")
    assert res_export.status_code == 200
    assert "text/csv" in res_export.headers.get("content-type", "")
    csv_text = res_export.text
    lines = csv_text.strip().split("\r\n") if "\r\n" in csv_text else csv_text.strip().split("\n")
    assert lines[0] == "run_id,scenario_id,algorithm,status,employee_id,unit_id,shift_id,hours"
    assert len(lines) > 1  # Contains assignment rows

    # 7. Non-existent run
    res_bad_run = await async_client.get("/api/schedules/non_existent_run")
    assert res_bad_run.status_code == 404
    assert res_bad_run.json()["errors"][0]["code"] == "RUN_NOT_FOUND"


@pytest.mark.asyncio
async def test_schedules_solve_validation_failure(async_client: AsyncClient):
    # Create invalid scenario (e.g. unknown shift ref)
    invalid_scn = {
        "id": "scn_invalid_solve",
        "name": "Invalid Scenario",
        "employees": [
            {
                "id": "E1",
                "name": "Worker 1",
                "skills": ["assembly"],
                "available_shifts": ["NON_EXISTENT_SHIFT"],
                "max_hours": 8.0,
            }
        ],
        "units": [{"id": "U1", "name": "Unit 1", "required_skills": []}],
        "shifts": [
            {
                "id": "S1",
                "name": "Shift 1",
                "start_time": "08:00",
                "end_time": "16:00",
                "duration_hours": 8.0,
            }
        ],
        "demands": [{"unit_id": "U1", "shift_id": "S1", "required_headcount": 1}],
    }
    res_create = await async_client.post("/api/scenarios", json=invalid_scn)
    assert res_create.status_code == 201

    solve_req = {
        "scenario_id": "scn_invalid_solve",
        "algorithm": "greedy",
    }
    res_solve = await async_client.post("/api/schedules/solve", json=solve_req)
    # Validation failure must return 422 with structured errors
    assert res_solve.status_code == 422
    err_body = res_solve.json()
    assert "errors" in err_body
    assert any(e["code"] == "UNKNOWN_REF" for e in err_body["errors"])
