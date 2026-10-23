from pydantic import BaseModel, field_validator


class EmployeeCreate(BaseModel):
    id: str
    name: str
    skills: list[str] = []
    available_shifts: list[str] = []
    max_hours: float

    @field_validator("max_hours")
    @classmethod
    def positive_hours(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("max_hours must be positive")
        return v


class EmployeeResponse(BaseModel):
    id: str
    name: str
    skills: list[str]
    available_shifts: list[str]
    max_hours: float
