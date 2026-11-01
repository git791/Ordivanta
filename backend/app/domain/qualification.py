"""
Qualification policy evaluation for workforce scheduling.

Provides a single `is_qualified(employee, unit, policy)` function used by:
- MILPScheduler (eligibility filtering)
- GreedyScheduler (candidate selection)
- ALNSScheduler (neighbourhood repair)
- Independent schedule validator (post-solve verification)

Policy semantics:
    ANY (default):
        Employee must possess at least one of the unit's required_skills.
        Preserves original backward-compatible behaviour.

    ALL:
        Employee must possess every skill listed in unit.required_skills.
        If mandatory_skill_requirements is non-empty, those take precedence over
        the simple required_skills list.

    LEVEL_AND_CERTIFICATION:
        Employee must possess every mandatory skill at or above the required
        proficiency level AND must hold every required certification.
        Falls back to ALL semantics if mandatory_skill_requirements is empty.

Overtime or on-call status never bypasses qualification requirements.
"""
from app.domain.models import Employee, ProductionUnit
from app.domain.enums import QualificationPolicy


def is_qualified(
    employee: Employee,
    unit: ProductionUnit,
    policy: QualificationPolicy = QualificationPolicy.ANY,
) -> bool:
    """
    Return True if the employee is qualified to work in the given production unit
    under the specified policy.

    Parameters
    ----------
    employee : Employee
        The employee to evaluate.
    unit : ProductionUnit
        The production unit requiring skills.
    policy : QualificationPolicy
        The qualification evaluation policy.

    Returns
    -------
    bool
        True iff the employee meets the unit's qualification requirements.
    """
    # Units with no skill requirements accept any employee under all policies.
    if not unit.required_skills and not unit.mandatory_skill_requirements:
        return True

    emp_skill_set = set(employee.skills)

    if policy == QualificationPolicy.ANY:
        # At least one matching skill (original disjunctive rule).
        return bool(emp_skill_set & set(unit.required_skills))

    elif policy == QualificationPolicy.ALL:
        if unit.mandatory_skill_requirements:
            # ALL mandatory skills must be present (level not enforced here).
            required = {req.skill for req in unit.mandatory_skill_requirements}
        else:
            required = set(unit.required_skills)
        return required.issubset(emp_skill_set)

    elif policy == QualificationPolicy.LEVEL_AND_CERTIFICATION:
        if unit.mandatory_skill_requirements:
            # Every mandatory skill must be present at >= required proficiency level.
            for req in unit.mandatory_skill_requirements:
                if req.skill not in emp_skill_set:
                    return False
                emp_level = employee.skill_levels.get(req.skill, 1)
                if emp_level < req.min_level:
                    return False
        else:
            # Fall back: require all skills listed (levels not enforced without requirements).
            if not set(unit.required_skills).issubset(emp_skill_set):
                return False

        # Check certifications.
        if unit.required_certifications:
            emp_certs = set(employee.certifications)
            if not set(unit.required_certifications).issubset(emp_certs):
                return False

        return True

    # Unrecognised policy: default to ANY for safety.
    return bool(emp_skill_set & set(unit.required_skills))


def qualification_gap_reason(
    employee: Employee,
    unit: ProductionUnit,
    policy: QualificationPolicy = QualificationPolicy.ANY,
) -> str | None:
    """
    Return a human-readable reason why the employee does not qualify, or None if qualified.
    Used by the independent validator to generate diagnostic shortage explanations.
    """
    if is_qualified(employee, unit, policy):
        return None

    emp_skill_set = set(employee.skills)

    if policy == QualificationPolicy.ANY:
        return (
            f"Employee '{employee.id}' has none of the required skills "
            f"{unit.required_skills}; has {employee.skills}"
        )

    elif policy in (QualificationPolicy.ALL, QualificationPolicy.LEVEL_AND_CERTIFICATION):
        if unit.mandatory_skill_requirements:
            missing_skills = []
            low_level_skills = []
            for req in unit.mandatory_skill_requirements:
                if req.skill not in emp_skill_set:
                    missing_skills.append(req.skill)
                elif policy == QualificationPolicy.LEVEL_AND_CERTIFICATION:
                    emp_level = employee.skill_levels.get(req.skill, 1)
                    if emp_level < req.min_level:
                        low_level_skills.append(
                            f"{req.skill}(has={emp_level},need={req.min_level})"
                        )
            parts = []
            if missing_skills:
                parts.append(f"missing skills: {missing_skills}")
            if low_level_skills:
                parts.append(f"insufficient proficiency: {low_level_skills}")
            if policy == QualificationPolicy.LEVEL_AND_CERTIFICATION and unit.required_certifications:
                emp_certs = set(employee.certifications)
                missing_certs = list(set(unit.required_certifications) - emp_certs)
                if missing_certs:
                    parts.append(f"missing certifications: {missing_certs}")
            return f"Employee '{employee.id}': {'; '.join(parts)}"
        else:
            missing = list(set(unit.required_skills) - emp_skill_set)
            return f"Employee '{employee.id}' missing skills: {missing}"

    return f"Employee '{employee.id}' does not qualify under policy {policy.value}"
