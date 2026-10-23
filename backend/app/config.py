import json
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    allowed_origins: list[str] | str = ["http://localhost:3000"]
    database_url: str = "sqlite+aiosqlite:///./ordivanta.db"
    solver_name: str = "HiGHS"
    solver_time_limit: int = 60

    @field_validator("allowed_origins")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
