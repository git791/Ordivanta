from datetime import datetime
from fastapi import APIRouter
from app.config import settings
from app.optimization.solver_adapter import get_solver

router = APIRouter()


@router.get("/health")
def health_check():
    solver_available = False
    try:
        solver = get_solver()
        if hasattr(solver, "available"):
            solver_available = bool(solver.available())
        else:
            solver_available = True
    except Exception:
        solver_available = False

    return {
        "status": "ok",
        "solver_available": solver_available,
        "solver_name": settings.solver_name,
        "timestamp": datetime.utcnow().isoformat(),
    }
