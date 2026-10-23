import pulp
from .base import SolverUnavailableError
from app.config import settings
from app.domain.enums import SolverStatus


def get_solver(name: str | None = None, time_limit: int | None = None) -> pulp.LpSolver:
    solver_name = name or settings.solver_name
    tl = time_limit or settings.solver_time_limit
    try:
        if solver_name.upper() == "HIGHS":
            # Attempt to use in-process Python binding first (highspy via pulp.getSolver)
            try:
                return pulp.getSolver("HiGHS", timeLimit=tl, msg=False)
            except Exception:
                return pulp.HiGHS_CMD(timeLimit=tl, msg=False)
        elif solver_name.upper() == "CBC":
            try:
                return pulp.getSolver("CBC", timeLimit=tl, msg=False)
            except Exception:
                return pulp.PULP_CBC_CMD(timeLimit=tl, msg=False)
        else:
            return pulp.getSolver(solver_name, timeLimit=tl, msg=False)
    except SolverUnavailableError:
        raise
    except Exception as e:
        raise SolverUnavailableError(f"Solver '{solver_name}' is not available: {e}") from e


def map_pulp_status(lp_status: int | None, sol_status: int | None = None) -> tuple[SolverStatus, str | None]:
    """Return (SolverStatus, message)."""
    # lp_status: 1=Optimal, -1=Infeasible, -2=Unbounded, -3=Undefined, 0=Not solved
    # sol_status: 1=Optimal, 2=Feasible, 0=Infeasible/not solved
    if lp_status == 1 and (sol_status == 1 or sol_status is None):
        return SolverStatus.OPTIMAL, None
    elif sol_status == 2 or (lp_status == 1 and sol_status == 2):
        return SolverStatus.FEASIBLE, "Feasible solution found but optimality not proven"
    elif lp_status == -1 or sol_status == -1:
        return SolverStatus.INFEASIBLE, "Problem is infeasible"
    elif lp_status == 0 or sol_status == 0:
        return SolverStatus.NOT_SOLVED, "Solver returned without a usable solution"
    else:
        return SolverStatus.ERROR, f"Unexpected solver status: lp={lp_status}, sol={sol_status}"
