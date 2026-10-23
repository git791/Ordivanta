from enum import Enum


class SolverStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    NOT_SOLVED = "NOT_SOLVED"
    ERROR = "ERROR"


class Algorithm(str, Enum):
    MILP = "milp"
    GREEDY = "greedy"


class ObjectivePrimary(str, Enum):
    FEASIBILITY = "feasibility"
    COST = "cost"
    FAIRNESS = "fairness"
