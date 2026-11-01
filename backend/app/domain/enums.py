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
    ALNS = "alns"


class ObjectivePrimary(str, Enum):
    FEASIBILITY = "feasibility"
    COST = "cost"
    FAIRNESS = "fairness"


class QualificationPolicy(str, Enum):
    """
    Controls how employee skill qualification is evaluated against unit requirements.

    ANY (default):
        Employee qualifies if they possess at least one of the unit's required_skills.
        Rationale: manufacturing cells with multiple acceptable skill profiles.
        Preserves backward-compatible behaviour.

    ALL:
        Employee must possess every skill listed in unit.required_skills.
        Use for roles requiring a specific combination of competencies.

    LEVEL_AND_CERTIFICATION:
        Employee must possess every mandatory skill at the required proficiency
        level AND hold every required certification.
        Use for safety-critical specialist roles.
    """
    ANY = "ANY"
    ALL = "ALL"
    LEVEL_AND_CERTIFICATION = "LEVEL_AND_CERTIFICATION"
